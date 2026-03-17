import sys
import os
import json
import inspect
import asyncio
from typing import Callable, Dict, Any, List, Optional, Union
from pydantic import validate_call
from .types import AgentResponse
from ..ui.interaction import prompt_approval_via_browser

class Skill:
    """
    The main interface for building SILO skills.
    """
    def __init__(self, namespace: str):
        self.namespace: str = namespace
        self.tools: Dict[str, Callable] = {}
        self._instructions: str = ""
        self._tool_metadata: Dict[str, Dict[str, Any]] = {}

    def tool(self, require_approval: bool = False, time_to_live: int = 600):
        """
        Decorator to register a tool (function) with SILO.
        """
        def decorator(func: Callable):
            # We use pydantic's validate_call to handle type validation automatically
            validated_func = validate_call(func)
            self.tools[func.__name__] = validated_func
            self._tool_metadata[func.__name__] = {
                "require_approval": require_approval,
                "time_to_live": time_to_live,
                "doc": func.__doc__ or ""
            }
            return func
        return decorator

    def instructions(self):
        """
        Decorator to register the philosophical/system instructions for the skill.
        """
        def decorator(func: Callable[[], str]):
            self._instructions = func()
            return func
        return decorator

    def run(self):
        """
        Entrypoint for the skill when executed as a script.
        Handles CLI arguments passed by the SILO Runner.
        """
        if len(sys.argv) < 2:
            print(f"SILO Skill: {self.namespace}")
            print("Available tools:", ", ".join(self.tools.keys()))
            return

        tool_name = sys.argv[1]

        # Metadata discovery flag
        if tool_name == "--silo-metadata":
            metadata = {
                "namespace": self.namespace,
                "instructions": self._instructions,
                "tools": {}
            }
            tools_meta: Dict[str, Any] = metadata["tools"] # type: ignore
            for name, meta in self._tool_metadata.items():
                tools_meta[name] = {
                    "description": str(meta.get("doc", "")),
                    "require_approval": bool(meta.get("require_approval", False)),
                    "time_to_live": int(meta.get("time_to_live", 600)),
                }
            print(json.dumps(metadata))
            return

        if tool_name not in self.tools:
            print(json.dumps({"status": "error", "error_message": f"Tool '{tool_name}' not found."}))
            sys.exit(1)

        # Parse kwargs from CLI (simple --key value parsing)
        kwargs: Dict[str, Any] = {}
        i = 2
        while i < len(sys.argv):
            arg: str = sys.argv[i]
            if arg.startswith("--") and len(arg) > 2:
                key: str = arg[2:]
                if i + 1 < len(sys.argv):
                    value = sys.argv[i+1]
                    kwargs[key] = value
                    i += 2
                else:
                    kwargs[key] = True # Flag
                    i += 1
            else:
                i += 1

        # Execute the tool
        try:
            # Check for approval requirement
            meta = self._tool_metadata.get(tool_name, {})
            if meta.get("require_approval"):
                if not self._request_approval(tool_name, kwargs):
                    print(json.dumps({
                        "status": "error",
                        "error_type": "SILO_APPROVAL_REQUIRED",
                        "error_message": "User rejected the action or approval timed out."
                    }))
                    sys.exit(1)

            # The tool is already wrapped in validate_call, so it will cast types automatically
            result = self.tools[tool_name](**kwargs)
            
            if isinstance(result, AgentResponse):
                print(result.to_json())
            else:
                # Fallback for simple return types
                print(json.dumps({"llm_text": str(result), "status": "success"}))
        except Exception as e:
            # Pydantic validation errors or runtime errors
            print(json.dumps({"status": "error", "error_message": str(e)}))
            sys.exit(1)

    def _request_approval(self, tool_name: str, kwargs: Dict[str, Any]) -> bool:
        """Request user approval via TTY or Browser."""
        if os.environ.get("SILO_HEADLESS") == "1":
            return False

        # 1. TTY Prompt
        if sys.stdin.isatty():
            try:
                from rich.prompt import Confirm
                from rich.console import Console
                from rich.panel import Panel
                console = Console()
                console.print(Panel(
                    f"Action: [bold]{tool_name}[/bold]\nArgs: {json.dumps(kwargs, indent=2)}",
                    title="[bold yellow]⚠️  Approval Required[/bold yellow]",
                    expand=False
                ))
                return Confirm.ask("Proceed?")
            except (KeyboardInterrupt, EOFError):
                return False

        # 2. Browser Prompt (Fallback)
        try:
            return prompt_approval_via_browser(self.namespace, tool_name, kwargs)
        except Exception:
            return False

