import argparse
import sys
import os
from pathlib import Path


def create_init_parser(subparsers):
    parser = subparsers.add_parser("init", help="Create a new SILO skill from a template")
    parser.add_argument("name", help="Name of the file to create (e.g., github_skill.py)")
    parser.add_argument("--secrets", help="Comma-separated list of required secret keys")


def handle_init(args):
    filename = args.name
    if not filename.endswith(".py"):
        filename += ".py"
        
    if os.path.exists(filename):
        print(f"Error: File '{filename}' already exists.", file=sys.stderr)
        sys.exit(1)
        
    secrets = []
    if args.secrets:
        secrets = [s.strip() for s in args.secrets.split(",")]
        
    # Generate the PEP 723 header
    content = [
        "# /// script",
        '# requires-python = ">=3.9"',
        '# dependencies = [',
        '#     "silo",',
        '# ]',
        "# ///",
        "",
        "from typing import Optional",
        "from pydantic import BaseModel, Field",
        "from silo import Skill, Secret, JSONResponse",
        "",
        "app = Skill(name=\"My Skill\", description=\"A new SILO skill.\")",
        ""
    ]
    
    # Generate the stub command
    content.append("@app.command()")
    content.append("def do_something(param: str):")
    content.append('    """Does something awesome."""')
    
    for secret in secrets:
        content.append(f'    token = Secret.require("{secret}")')
        
    if not secrets:
        content.append('    # token = Secret.require("MY_API_KEY")')
        
    content.append('    return JSONResponse({"status": "success", "param": param})')
    content.append("")
    
    # Generate the entrypoint
    content.append('if __name__ == "__main__":')
    content.append('    app.run()')
    content.append("")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
        
    print(f"Successfully created '{filename}'!")
    print(f"To run it: uv run {filename} do_something --param value")


def create_test_parser(subparsers):
    parser = subparsers.add_parser("test", help="Simulate agent execution of a SILO skill")
    parser.add_argument("script", help="Path to the skill script (e.g., skill.py)")
    parser.add_argument("cmd_args", nargs=argparse.REMAINDER, help="Command and arguments to pass to the skill")


def handle_test(args):
    import subprocess
    import json
    
    script = args.script
    if not os.path.exists(script):
        print(f"Error: Script '{script}' not found.", file=sys.stderr)
        sys.exit(1)
        
    print(f"🧪 Testing SILO skill: {script}\n")
    
    # Prepare headless environment
    env = os.environ.copy()
    env["SILO_HEADLESS"] = "1"
    # Remove real display variables to force headless secret fallback
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    
    cmd_base = [sys.executable, script]
    
    # 1. Test Manifest Generation
    print("[1/2] Verifying manifest generation (--silo-manifest)... ", end="")
    res = subprocess.run(cmd_base + ["--silo-manifest"], env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print("❌ FAILED")
        print(f"Stderr: {res.stderr}")
        sys.exit(1)
    if not res.stdout.strip().startswith("#"):
        print("❌ FAILED (Output is not Markdown)")
        sys.exit(1)
    print("✅ OK")
    
    # 2. Test Execution
    if not args.cmd_args:
        print("\n⚠️ No command arguments provided, skipping execution test.")
        print(f"  To test execution, run: silo test {script} <command> [--args...]")
        return
        
    cmd_str = " ".join(args.cmd_args)
    print(f"[2/2] Verifying execution: `{' '.join(cmd_base + args.cmd_args)}`... ", end="")
    
    # Note: subprocess.run captures output, so sys.stdin.isatty() will be False in the child process.
    res = subprocess.run(cmd_base + args.cmd_args, env=env, capture_output=True, text=True)
    
    # Process output
    stdout = res.stdout.strip()
    
    if res.returncode != 0:
        # Check if it's our expected JSON error
        try:
            err_data = json.loads(stdout)
            if err_data.get("error") == "SILO_AUTH_REQUIRED":
                print("✅ OK (Headless Auth Error correctly triggered)")
                return
            if err_data.get("error") == "SILO_APPROVAL_REQUIRED":
                print("✅ OK (Headless Approval Error correctly triggered)")
                return
        except json.JSONDecodeError:
            pass
            
        print(f"❌ FAILED (Exit code {res.returncode})")
        if stdout: print(f"Stdout:\n{stdout}")
        if res.stderr: print(f"Stderr:\n{res.stderr}")
        sys.exit(1)
        
    # Standard success - Check if output is clean JSON
    try:
        json.loads(stdout)
        print("✅ OK (Valid JSON output)")
    except json.JSONDecodeError:
        print("✅ OK (Text output)")
        
    if stdout:
        print(f"\nResponse:\n{stdout}")


def create_doctor_parser(subparsers):
    parser = subparsers.add_parser("doctor", help="Check the health of the SILO environment")


def handle_doctor(args):
    import platform
    import subprocess
    import shutil
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    console.print(Panel("🩺 [bold cyan]SILO Environment Doctor[/bold cyan]", expand=False))

    table = Table(show_header=False, box=None)
    
    # 1. Platform & Python
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    table.add_row("Python Version", f"[green]✅ {py_ver}[/green]" if sys.version_info >= (3, 9) else f"[red]❌ {py_ver} (Need 3.9+)[/red]")
    table.add_row("Platform", f"[blue]{platform.system()} {platform.release()}[/blue]")

    # 2. Keyring / Keychain
    try:
        import keyring
        name = keyring.get_keyring().name
        table.add_row("Keychain Backend", f"[green]✅ {name}[/green]")
    except Exception as e:
        table.add_row("Keychain Backend", f"[red]❌ Error: {str(e)}[/red]")

    # 3. 'uv' check
    uv_path = shutil.which("uv")
    if uv_path:
        try:
            uv_ver = subprocess.check_output(["uv", "--version"], text=True).strip()
            table.add_row("uv Package Manager", f"[green]✅ {uv_ver}[/green]")
        except:
            table.add_row("uv Package Manager", "[yellow]⚠️ Found but failed to get version[/yellow]")
    else:
        table.add_row("uv Package Manager", "[yellow]⚠️ Not found (Recommended for S.I.L.O isolation)[/yellow]")

    # 4. Optional Deps
    try:
        import mcp
        table.add_row("MCP Support", "[green]✅ Installed[/green]")
    except ImportError:
        table.add_row("MCP Support", "[yellow]⚠️ Not installed (pip install 'silo[mcp]')[/yellow]")

    try:
        import pydantic
        table.add_row("Pydantic Support", "[green]✅ Installed[/green]")
    except ImportError:
        table.add_row("Pydantic Support", "[red]❌ Missing (Critical dependency)[/red]")

    console.print(table)
    console.print("\n[bold]Next Steps:[/bold]")
    if not uv_path:
        console.print("- Install [bold]uv[/bold] for better skill isolation: [dim]https://github.com/astral-sh/uv[/dim]")
    console.print("- Run [bold]silo init[/bold] to create your first skill.")
    console.print("- Use [bold]silo test <script>[/bold] to verify agent compatibility.")


def main():
    parser = argparse.ArgumentParser(prog="silo", description="SILO Framework CLI utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    create_init_parser(subparsers)
    create_test_parser(subparsers)
    create_doctor_parser(subparsers)
    
    args = parser.parse_args()
    
    if args.command == "init":
        handle_init(args)
    elif args.command == "test":
        handle_test(args)
    elif args.command == "doctor":
        handle_doctor(args)

if __name__ == "__main__":
    main()
