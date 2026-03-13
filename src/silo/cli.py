import typer
import os
import sys
import json
import shutil
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .hub import HubManager

app = typer.Typer(help="SILO: Agentic Operating System CLI")
console = Console()
hub = HubManager()

@app.command()
def init(
    name: str = typer.Argument(..., help="Name of the skill to initialize"),
    path: Path = typer.Option(Path("."), help="Path to create the skill in"),
    secrets: Optional[str] = typer.Option(None, "--secrets", "-s", help="Comma-separated list of required secrets")
):
    """
    Initialize a new SILO skill with boilerplate code and .siloignore.
    """
    skill_dir = path / name
    if skill_dir.exists():
        console.print(f"[red]Error:[/red] Directory '{skill_dir}' already exists.")
        raise typer.Exit(code=1)

    skill_dir.mkdir(parents=True)
    
    # Prepare secrets boilerplate
    secret_imports = ""
    secret_calls = ""
    if secrets:
        secret_list = [s.strip() for s in secrets.split(",")]
        secret_imports = "from silo.secrets import require as require_secret"
        for s in secret_list:
            secret_calls += f'\n    # This key is required for the tool below\n    # It will be fetched from Keychain, Env, or prompted via browser.\n    {s.lower()}_key = require_secret("{s}")'

    # Create skill.py
    skill_py = skill_dir / "skill.py"
    skill_py.write_text(f"""# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "silo",
#     "requests",
# ]
# ///

import requests
from silo.skill import Skill
{secret_imports}
from silo.types import AgentResponse

skill = Skill(namespace="{name}")

@skill.instructions()
def instructions():
    return \"\"\"
    Describe the philosophical purpose and usage of this skill here.
    The Agent will read this to understand how to use the tools.
    \"\"\"

@skill.tool()
def hello(name: str):
    \"\"\"A simple greeting tool.\"\"\"
    {secret_calls}
    return AgentResponse(llm_text=f"Hello, {{name}}!", raw_data={{"status": "ok"}})

if __name__ == "__main__":
    skill.run()
""")

    # Create .siloignore
    siloignore = skill_dir / ".siloignore"
    siloignore.write_text("""# SILO ignore file
__pycache__/
*.pyc
.venv/
.git/
.DS_Store
*.log
""")

    console.print(f"[green]Successfully initialized skill '{name}' in {skill_dir}[/green]")
    console.print(f"To get started, edit [bold]{skill_py}[/bold]")

@app.command()
def install(
    source: str = typer.Argument(..., help="Local path or registry name to install"),
    namespace: Optional[str] = typer.Option(None, "--name", "-n", help="Override the namespace for this skill")
):
    """
    Install a skill into the local SILO hub.
    """
    source_path = Path(source)
    if not source_path.exists():
        console.print(f"[red]Error:[/red] Local path '{source}' does not exist.")
        raise typer.Exit(code=1)

    # Detect namespace: Flag > Code Analysis > Folder Name
    if not namespace:
        # Try to peek into skill.py for Skill(namespace="...")
        skill_file = source_path / "skill.py" if source_path.is_dir() else source_path
        if skill_file.exists():
            import re
            content = skill_file.read_text()
            match = re.search(r'Skill\(namespace=["\']([^"\']+)["\']\)', content)
            if match:
                namespace = match.group(1)
    
    if not namespace:
        namespace = source_path.name

    hub.install_local(source_path, namespace)
    console.print(f"[green]Successfully installed skill as [bold]{namespace}[/bold] to hub.[/green]")

    # Auto-inspect to prime the search cache AND create .venv
    from .runner import Runner
    runner = Runner()
    with console.status(f"[bold cyan]Preparing environment for {namespace}...[/bold cyan]", spinner="dots"):
        # 1. Fetch metadata
        result = asyncio.run(runner.execute(namespace, "--silo-metadata", {}))
        if result.get("status") != "error":
            hub.save_metadata(namespace, result)
        
        # 2. Create/Sync local .venv
        asyncio.run(runner.precache(namespace))

@app.command()
def ps():
    """
    List all installed skills in the local hub.
    """
    skills = hub.list_skills()
    if not skills:
        console.print("No skills installed in hub.")
        return

    def format_size(size_bytes_int: int) -> str:
        size: float = float(size_bytes_int)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    table = Table(title="Installed SILO Skills")
    table.add_column("Namespace", style="cyan")
    table.add_column("Size (Src)", justify="right")
    table.add_column("Size (Env)", justify="right")
    table.add_column("Last Used", style="magenta")

    for ns in skills:
        last_used = hub.get_last_used(ns)
        last_used_str = last_used.strftime("%Y-%m-%d %H:%M") if last_used else "Never"
        
        usage = hub.get_disk_usage(ns)
        src_size = format_size(usage["source"])
        env_size = format_size(usage["venv"])
        
        table.add_row(ns, src_size, env_size, last_used_str)

    console.print(table)

@app.command()
def remove(
    namespace: str = typer.Argument(..., help="Namespace of the skill to remove")
):
    """
    Remove a skill from the local hub.
    """
    if not hub.is_installed(namespace):
        console.print(f"[red]Error:[/red] Skill '{namespace}' is not installed.")
        raise typer.Exit(code=1)

    hub.remove(namespace)
    console.print(f"[green]Successfully removed '{namespace}' from hub.[/green]")

@app.command()
def run(
    namespace: str = typer.Argument(..., help="Namespace of the skill"),
    tool: str = typer.Argument(..., help="Tool name to execute"),
    args: List[str] = typer.Argument(None, help="Arguments to pass to the tool")
):
    """
    Manually execute a skill tool from the hub.
    """
    from .runner import Runner
    runner = Runner()
    
    # Simple parsing of key=value pairs from args
    kwargs: Dict[str, Any] = {}
    if args:
        for a in args:
            if "=" in a:
                k, v = a.split("=", 1)
                kwargs[k] = v
            else:
                kwargs[a] = True

    with console.status(f"[bold cyan]Executing {namespace}:{tool}...[/bold cyan]", spinner="dots"):
        result = asyncio.run(runner.execute(namespace, tool, kwargs))
    
    if result.get("status") == "error":
        msg = result.get("error_message") or result.get("message") or result.get("stderr") or "Unknown error"
        console.print(f"[red]Error:[/red] {msg}")
        raise typer.Exit(code=1)
        
    console.print(Panel(result.get("llm_text", json.dumps(result)), title="Execution Result"))

@app.command()
def test(
    namespace: str = typer.Argument(..., help="Namespace of the skill to test"),
    tool: str = typer.Argument(..., help="Tool name to execute"),
    args: List[str] = typer.Argument(None, help="Arguments to pass to the tool (key=value)")
):
    """
    Simulate a headless agent execution to verify skill output.
    """
    from .runner import Runner
    runner = Runner()
    
    kwargs: Dict[str, Any] = {}
    if args:
        for a in args:
            if "=" in a:
                k, v = a.split("=", 1)
                kwargs[k] = v
            else:
                kwargs[a] = True

    # Force headless mode to verify secret fallbacks/approvals
    os.environ["SILO_HEADLESS"] = "1"
    
    with console.status(f"[bold yellow]Testing {namespace}:{tool}...[/bold yellow]", spinner="dots"):
        result = asyncio.run(runner.execute(namespace, tool, kwargs))
    
    # 1. Check if result is valid JSON
    try:
        json_output = json.dumps(result, indent=2)
        console.print("[green]PASS:[/green] Output is valid JSON")
    except Exception as e:
        console.print(f"[red]FAIL:[/red] Invalid JSON output: {e}")
        raise typer.Exit(code=1)

    # 2. Check for SILO status
    status = result.get("status", "unknown")
    if status == "success":
        console.print("[green]PASS:[/green] Tool executed successfully")
    elif status == "error":
        err_type = result.get("error_type", "UNKNOWN_ERROR")
        console.print(f"[red]FAIL:[/red] Tool returned error status: {err_type}")
        console.print(f"Message: {result.get('error_message')}")
        raise typer.Exit(code=1)
    
    console.print(Panel(json_output, title="Test Result (JSON)"))

@app.command()
def doctor():
    """
    Check system health and dependencies for S.I.L.O.
    """
    from .security import SecurityManager
    import platform
    
    table = Table(title="S.I.L.O Environment Doctor", show_header=False)
    table.add_column("Check", style="cyan")
    table.add_column("Status")

    # 1. Python Version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    table.add_row("Python Version", py_ver)

    # 2. Platform
    table.add_row("Platform", f"{platform.system()} {platform.release()}")

    # 3. uv check
    uv_path = shutil.which("uv")
    if uv_path:
        table.add_row("uv Package Manager", f"[green]Found at {uv_path}[/green]")
    else:
        table.add_row("uv Package Manager", "[red]Not found. Please install uv (https://astral.sh/uv)[/red]")

    # 4. Keychain check
    try:
        import keyring
        storage = keyring.get_keyring().name
        table.add_row("Secure Storage (Keychain)", f"[green]Available ({storage})[/green]")
    except Exception as e:
        table.add_row("Secure Storage (Keychain)", f"[red]Error: {e}[/red]")

    # 5. Hub directory
    silo_dir = Path.home() / ".silo"
    if silo_dir.exists():
        table.add_row("Hub Directory", f"[green]Exists at {silo_dir}[/green]")
    else:
        table.add_row("Hub Directory", "[yellow]Not initialized (will be created on first install)[/yellow]")

    console.print(table)

@app.command()
def inspect(
    namespace: str = typer.Argument(..., help="Namespace of the skill to inspect")
):
    """
    Display instructions and metadata for an installed skill.
    """
    from .runner import Runner
    runner = Runner()
    
    with console.status(f"[bold cyan]Inspecting {namespace}...[/bold cyan]", spinner="dots"):
        # We use the special internal flag to get full metadata
        result = asyncio.run(runner.execute(namespace, "--silo-metadata", {}))
    
    if result.get("status") == "error":
        msg = result.get("error_message") or result.get("message") or result.get("stderr") or "Unknown error"
        console.print(f"[red]Error:[/red] {msg}")
        raise typer.Exit(code=1)
    
    # Format and display the metadata
    instructions = result.get("instructions", "No instructions provided.")
    tools = result.get("tools", {})
    
    # Cache for search engine
    hub.save_metadata(namespace, result)
    
    console.print(Panel(instructions, title=f"Skill: {namespace} (Instructions)", border_style="cyan"))
    
    if tools:
        table = Table(title="Available Tools", show_header=True, header_style="bold magenta")
        table.add_column("Tool Name", style="bold")
        table.add_column("Description")
        table.add_column("Approvals", justify="center")
        
        for name, meta in tools.items():
            approval = "[yellow]Required[/yellow]" if meta.get("require_approval") else "[green]Auto[/green]"
            table.add_row(name, meta.get("description", ""), approval)
        
        console.print(table)
    else:
        console.print("[yellow]No tools found in this skill.[/yellow]")
@app.command()
def precache(
    namespace: str = typer.Argument(..., help="Namespace of the skill to precache")
):
    """
    Pre-download dependencies for a skill using 'uv'.
    """
    from .runner import Runner
    runner = Runner()
    console.print(f"Precaching dependencies for [bold]{namespace}[/bold]...")
    success = asyncio.run(runner.precache(namespace))
    if success:
        console.print("[green]Successfully precached.[/green]")
    else:
        console.print("[red]Failed to precache.[/red]")

@app.command(name="mcp-run")
def mcp_run():
    """
    Start the SILO MCP server (STDIO).
    """
    from .mcp_server import SiloMCPServer
    console.print("[bold cyan]Starting SILO MCP Server...[/bold cyan]")
    server = SiloMCPServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        pass

@app.command()
def auth(
    action: str = typer.Argument(..., help="Action: set, map"),
    key: str = typer.Argument(..., help="Secret key name"),
    value: str = typer.Argument(None, help="Secret value (for 'set')")
):
    """
    Manage encrypted secrets and Keyring mappings.
    """
    from .security import SecurityManager
    sm = SecurityManager()
    
    if action == "set":
        if not value:
            console.print("[red]Error:[/red] Value required for 'set' action.")
            raise typer.Exit(1)
        # For simplicity, we store in one file for now
        secrets = sm.load_credentials()
        secrets[key] = value
        sm.save_credentials(secrets)
        console.print(f"[green]Secret '{key}' encrypted and saved locally.[/green]")
    elif action == "map":
        # Placeholder for silo.yaml mapping
        console.print(f"Mapping logic for '{key}' not yet implemented.")

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (semantic or exact)")
):
    """
    Search for tools across all installed skills using BM25.
    """
    from .search import SearchEngine
    se = SearchEngine()
    
    with console.status(f"[bold cyan]Searching for '{query}'...[/bold cyan]", spinner="dots"):
        results = asyncio.run(se.search(query))
    
    if not results:
        console.print(f"No results found for '[yellow]{query}[/yellow]'.")
        return

    table = Table(title=f"Search results for '{query}'")
    table.add_column("Tool (ID)", style="bold cyan")
    table.add_column("Description")
    
    for res in results:
        table.add_row(res["full_id"], res["description"])
    
    console.print(table)

def main():
    app()

if __name__ == "__main__":
    main()

