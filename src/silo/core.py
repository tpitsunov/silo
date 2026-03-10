import argparse
import inspect
import sys
import json
import traceback

class Skill:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.commands = {}

    def command(self, name: str = None):
        """Decorator to register a function as a skill command."""
        def decorator(func):
            cmd_name = name or func.__name__
            self.commands[cmd_name] = func
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
                                        import json
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
            import os
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
        asyncio.run(server.run_stdio_async())
