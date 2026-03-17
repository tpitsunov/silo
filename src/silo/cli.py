import os
import sys
import json
import shutil
import asyncio
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .core.hub import HubManager

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
    secret_calls = ""
    if secrets:
        secret_list = [s.strip() for s in secrets.split(",")]
        secret_imports = "from silo import require_secret"
        for s in secret_list:
            comment = '\n    # This key is required for the tool below\n' \
                      '    # It will be fetched from Keychain, Env, or prompted via browser.\n'
            secret_calls += f'{comment}    {s.lower()}_key = require_secret("{s}")'
    else:
        secret_imports = ""

    # Create skill.py
    skill_py = skill_dir / "skill.py"
    skill_py.write_text(f'''# /// script
# requires-python = ">=3.9"
# dependencies = ["silo-framework"]
# ///
from silo import Skill, AgentResponse
{secret_imports}

skill = Skill(namespace='{name}')

@skill.instructions()
def instructions():
    return """
    Describe the philosophical purpose and usage of this skill here.
    The Agent will read this to understand how to use the tools.
    """

@skill.tool()
def hello(name: str):
    """A simple greeting tool."""
    {secret_calls}
    return AgentResponse(llm_text=f"Hello, {{name}}!", raw_data={{"status": "ok"}})

if __name__ == "__main__":
    skill.run()
''')

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
    namespace: Optional[str] = typer.Option(None, "--name", "-n", help="Override the namespace for this skill"),
    remote: str = typer.Option("default", "--remote", "-r", help="Target remote registry name")
):
    """
    Install a skill into the local SILO hub.
    """
    source_path = Path(source)
    namespace_override = namespace
    if not source_path.exists():
        # Try Registry install
        from .services.registry import RegistryManager
        reg = RegistryManager()

        with console.status(f"[bold cyan]Fetching {source} from remote '{remote}'...[/bold cyan]", spinner="dots"):
            metadata = reg.get_skill_metadata(source, remote_name=remote)
            if not metadata:
                console.print(f"[red]Error:[/red] Skill '{source}' not found locally or in remote '{remote}'.")
                raise typer.Exit(code=1)

            # Download to a temporary location first or directly to hub
            temp_dir = Path(tempfile.gettempdir()) / f"silo_{source}"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            if reg.download_skill(source, temp_dir, remote_name=remote):
                source_path = temp_dir
                if not namespace_override:
                    namespace_override = source
            else:
                console.print(f"[red]Error:[/red] Failed to download '{source}' from remote '{remote}'.")
                raise typer.Exit(code=1)

    # Detect namespace: Flag > Code Analysis > Folder Name
    if not namespace_override:
        # Try to peek into skill.py for Skill(namespace="...")
        skill_file = source_path / "skill.py" if source_path.is_dir() else source_path
        if skill_file.exists():
            import re
            content = skill_file.read_text(encoding="utf-8")
            match = re.search(r'Skill\(namespace=["\']([^"\']+)["\']\)', content)
            if match:
                namespace_override = match.group(1)

    if not namespace_override:
        namespace_override = source_path.name

    hub.install_local(source_path, namespace_override)
    console.print(f"[green]Successfully installed skill as [bold]{namespace_override}[/bold] to hub.[/green]")

    # Auto-inspect to prime the search cache AND create .venv
    from .core.runner import Runner
    runner = Runner()
    with console.status(f"[bold cyan]Preparing environment for {namespace_override}...[/bold cyan]", spinner="dots"):
        # 1. Fetch metadata
        result = asyncio.run(runner.execute(namespace_override, "--silo-metadata", {}))
        if result.get("status") != "error":
            hub.save_metadata(namespace_override, result)

        # 2. Create/Sync local .venv
        asyncio.run(runner.precache(namespace_override))

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
    from .core.runner import Runner
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
    from .core.runner import Runner
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
    from .core.runner import Runner
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
    from .core.runner import Runner
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
    from .services.mcp_server import SiloMCPServer
    console.print("[bold cyan]Starting SILO MCP Server...[/bold cyan]")
    server = SiloMCPServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        pass

@app.command()
def auth(
    action: str = typer.Argument(..., help="Action: set, map, login"),
    key: str = typer.Argument(..., help="Secret key name or API token (for login)"),
    value: str = typer.Argument(None, help="Secret value (for 'set')"),
    remote: str = typer.Option("default", "--remote", "-r", help="Target remote registry for login")
):
    """
    Manage encrypted secrets, Keyring mappings, and Registry authentication.
    """
    from .security.security import SecurityManager
    sm = SecurityManager()

    if action == "login":
        from .services.registry import RegistryManager
        reg = RegistryManager()
        reg.set_token(key, remote_name=remote)
        console.print(f"[green]Successfully logged in to SILO Registry '{remote}'.[/green]")
        return

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
        console.print(f"Mapping logic for '{key}' is planned for a future release.")

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (semantic or exact)"),
    remote: Optional[str] = typer.Option(None, "--remote", "-r", help="Target remote registry (default: 'default')"),
    all_remotes: bool = typer.Option(False, "--all", "-a", help="Search across all configured remotes")
):
    """
    Search for tools locally or across the SILO ecosystem.
    """
    from .services.search import SearchEngine
    from .services.registry import RegistryManager
    se = SearchEngine()
    reg = RegistryManager()

    results = []
    with console.status(f"[bold cyan]Searching for '{query}'...[/bold cyan]", spinner="dots"):
        # 1. Local results
        results = asyncio.run(se.search(query))

        # 2. Remote results
        if all_remotes:
            for name in reg.remotes.keys():
                remote_results = reg.search(query, remote_name=name)
                results.extend(remote_results)
        elif remote:
            remote_results = reg.search(query, remote_name=remote)
            results.extend(remote_results)

    if not results:
        console.print(f"No results found for '[yellow]{query}[/yellow]'.")
        return

    table = Table(title=f"Search results for '{query}'")
    table.add_column("Source", style="dim")
    table.add_column("Tool (ID)", style="bold cyan")
    table.add_column("Description")

    for res in results:
        source = res.get("remote", "Local")
        table.add_row(source, res["full_id"], res["description"])

    console.print(table)

@app.command()
def publish(
    path: Path = typer.Argument(Path("."), help="Path to the skill directory"),
    namespace: Optional[str] = typer.Option(None, "--name", "-n", help="Namespace to publish as"),
    remote: str = typer.Option("default", "--remote", "-r", help="Target remote registry name")
):
    """
    Publish a local skill to the SILO Registry.
    """
    from .services.registry import RegistryManager
    from .core.runner import Runner
    reg = RegistryManager()
    runner = Runner()

    if not path.exists():
        console.print(f"[red]Error:[/red] Path {path} not found.")
        raise typer.Exit(1)

    # 1. Extract metadata
    with console.status("[bold cyan]Analyzing skill...[/bold cyan]", spinner="dots"):
        # We need the namespace to execute
        ns = namespace
        if not ns:
            skill_file = path / "skill.py" if path.is_dir() else path
            if skill_file.exists():
                import re
                content = skill_file.read_text(encoding="utf-8")
                match = re.search(r'Skill\(namespace=["\']([^"\']+)["\']\)', content)
                if match:
                    ns = match.group(1)

        if not ns:
            ns = path.name

        # Execute discovery in the current path
        # In this context, execute_path might be needed in Runner
        # For now, we assume it's installed or we use a temporary run
        metadata = asyncio.run(runner.execute(ns, "--silo-metadata", {}))

    if metadata.get("status") == "error":
        console.print(f"[red]Error analyzing skill:[/red] {metadata.get('error_message')}")
        raise typer.Exit(1)

    # 2. Upload
    with console.status(f"[bold cyan]Publishing {ns} to remote '{remote}'...[/bold cyan]", spinner="dots"):
        result = reg.publish(path if path.is_dir() else path.parent, metadata, remote_name=remote)

    if result.get("status") == "success":
        console.print(f"[green]Successfully published {ns} v{result.get('version', 'unknown')} to '{remote}'![/green]")
    else:
        console.print(f"[red]Error publishing to '{remote}':[/red] {result.get('message', 'Unknown error')}")
        raise typer.Exit(1)

@app.command(name="remote")
def remote_cmd(
    action: str = typer.Argument(..., help="Action: add, remove, list"),
    name: str = typer.Argument(None, help="Name of the remote"),
    url: str = typer.Argument(None, help="URL of the remote (for 'add')")
):
    """
    Manage remote SILO registries.
    """
    from .services.registry import RegistryManager
    reg = RegistryManager()

    if action == "add":
        if not name or not url:
            console.print("[red]Error:[/red] Both name and url are required for 'add'.")
            raise typer.Exit(1)
        reg.add_remote(name, url)
        console.print(f"[green]Remote '{name}' added: {url}[/green]")
    elif action == "remove":
        if not name:
            console.print("[red]Error:[/red] Remote name required for 'remove'.")
            raise typer.Exit(1)
        reg.remove_remote(name)
        console.print(f"[green]Remote '{name}' removed.[/green]")
    elif action == "list":
        table = Table(title="Configured SILO Remotes")
        table.add_column("Name", style="cyan")
        table.add_column("URL")
        for n, u in reg.remotes.items():
            table.add_row(n, u)
        console.print(table)

def main():
    app()

if __name__ == "__main__":
    main()
