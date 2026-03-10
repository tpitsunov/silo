import argparse
import inspect
import sys
import json
import traceback
import os

class Skill:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.commands = {}
        self.command_metadata = {}

    def command(self, name: str = None, require_approval: bool = False):
        """Decorator to register a function as a skill command."""
        def decorator(func):
            cmd_name = name or func.__name__
            self.commands[cmd_name] = func
            self.command_metadata[cmd_name] = {
                "require_approval": require_approval
            }
            return func
        return decorator

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog=self.name, description=self.description)
        # We manually check --silo-manifest first to avoid required args from blocking it,
        # but we add it to the parser for documentation.
        parser.add_argument("--silo-manifest", action="store_true", help="Generate SKILL.md manifest")
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        for cmd_name, func in self.commands.items():
            doc = inspect.getdoc(func) or ""
            cmd_parser = subparsers.add_parser(cmd_name, description=doc)
            
            sig = inspect.signature(func)
            for param_name, param in sig.parameters.items():
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
                
                # If it's a Pydantic BaseModel, argparse just needs to accept a string
                if inspect.isclass(param_type):
                    try:
                        from pydantic import BaseModel
                        if issubclass(param_type, BaseModel):
                            param_type = str
                    except ImportError:
                        pass
                
                kwargs = {
                    "type": param_type,
                    "help": f"{param_name} parameter"
                }
                if param.default != inspect.Parameter.empty:
                    kwargs["default"] = param.default
                else:
                    kwargs["required"] = True
                
                # Register argument as an option
                cmd_parser.add_argument(f"--{param_name}", **kwargs)
                
        return parser

    def run(self):
        """Main execution entrypoint for the CLI."""
        try:
            # Short-circuit for manifest generation
            if "--silo-manifest" in sys.argv:
                from .manifest import generate_manifest
                print(generate_manifest(self))
                sys.exit(0)
                
            parser = self._build_parser()
            args = parser.parse_args()
            
            if not args.command:
                parser.print_help()
                sys.exit(1)
                
            cmd_func = self.commands[args.command]
            sig = inspect.signature(cmd_func)
            
            # Extract arguments specific to the function
            func_args = {}
            for param_name, param in sig.parameters.items():
                if param_name in vars(args):
                    val = getattr(args, param_name)
                    # Handle Pydantic BaseModels
                    if inspect.isclass(param.annotation):
                        try:
                            from pydantic import BaseModel, ValidationError
                            if issubclass(param.annotation, BaseModel):
                                if isinstance(val, str):
                                    try:
                                        # Parse JSON string to pydantic model
                                        parsed_json = json.loads(val)
                                        val = param.annotation.model_validate(parsed_json)
                                    except ValidationError as e:
                                        print(json.dumps({
                                            "error": "Input Validation Error", 
                                            "details": e.errors()
                                        }))
                                        sys.exit(1)
                                    except json.JSONDecodeError:
                                        print(json.dumps({"error": f"Invalid JSON string for parameter '{param_name}'"}))
                                        sys.exit(1)
                        except ImportError:
                            pass # Pydantic not installed
                    
                    func_args[param_name] = val
            
            # Execute command
            if self.command_metadata.get(args.command, {}).get("require_approval"):
                if not self._request_approval(args.command, func_args):
                    print(json.dumps({
                        "error": "SILO_APPROVAL_REQUIRED",
                        "message": "This action requires human approval which was rejected or not available."
                    }))
                    sys.exit(1)

            result = cmd_func(**func_args)
            
            # Clean output serialization
            from .responses import SiloResponse
            if isinstance(result, SiloResponse):
                print(result.render())
            elif isinstance(result, (dict, list)):
                print(json.dumps(result, indent=2))
            elif result is not None:
                print(str(result))
                
        except SystemExit:
            # Let sys.exit() and argparse propagate normally
            raise
        except Exception as e:
            # Catch all unhandled exceptions and return safe JSON output
            error_data = {"error": str(e), "type": type(e).__name__}
            # Only print traceback if SILO_DEBUG is set for human dev
            if os.environ.get("SILO_DEBUG") == "1":
                traceback.print_exc()
            print(json.dumps(error_data))
            sys.exit(1)

    def run_mcp(self):
        """Start this skill as an MCP server (stdio transport)."""
        import asyncio
        from .mcp_adapter import create_mcp_server
        server = create_mcp_server(self)
    def _request_approval(self, cmd_name: str, args: dict) -> bool:
        """Request user approval for a critical action via TTY or Browser."""
        # 0. Early exit for headless / CI / Automated tests
        if os.environ.get("SILO_HEADLESS") == "1":
            return False

        # 1. TTY Prompt (rich.prompt)
        if sys.stdin.isatty():
            from rich.prompt import Confirm
            from rich.console import Console
            console = Console()
            console.print(f"\n[bold yellow]⚠️  Action Approval Required[/bold yellow]")
            console.print(f"Skill:    [bold]{self.name}[/bold]")
            console.print(f"Command:  [bold]{cmd_name}[/bold]")
            console.print(f"Arguments: {json.dumps(args, indent=2)}")
            try:
                return Confirm.ask("Do you want to proceed?")
            except (KeyboardInterrupt, EOFError):
                return False

        # 2. No TTY, but has Display → Browser (the SILO premium way)
        from .secrets import _has_display
        if _has_display():
            try:
                from .interaction import prompt_approval_via_browser
                return prompt_approval_via_browser(self.name, cmd_name, args)
            except Exception:
                pass 
        
        # 3. Headless, no TTY, no display → Structured rejection
        return False
