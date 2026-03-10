import os
import sys
import json
import getpass
import keyring
import keyring.errors
from rich.console import Console

console = Console()


def _has_display() -> bool:
    """Check if a graphical display is available (i.e., we can open a browser)."""
    if os.environ.get("SILO_HEADLESS") == "1":
        return False
    if sys.platform == "darwin":
        return True  # macOS always has a window server if user is logged in
    if sys.platform == "win32":
        return True
    # Linux: check for DISPLAY or WAYLAND_DISPLAY
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


class Secret:
    """Wrapper for OS Keychain to securely manage skill API keys."""
    
    SERVICE_NAME = "silo-agent"

    @classmethod
    def require(cls, key_name: str) -> str:
        """
        Retrieves a secret through a secure fallback chain:
        1. Environment variable (headless / CI / Docker)
        2. OS Keychain (persistent local storage)
        3. Browser auth page on localhost (secure, no LLM exposure)
        4. Interactive TTY prompt via getpass (manual terminal usage)
        5. Structured JSON error for truly headless environments
        """
        # 1. Environment Variable (headless / CI / Docker)
        env_token = os.environ.get(key_name)
        if env_token:
            return env_token

        # 2. OS Keychain
        try:
            token = keyring.get_password(cls.SERVICE_NAME, key_name)
            if token:
                return token
        except keyring.errors.KeyringError:
            pass

        # 3. Interactive TTY → getpass (user running script manually)
        if sys.stdin.isatty():
            console.print(f"[bold yellow]Secret '{key_name}' not found in environment or keychain.[/bold yellow]")
            try:
                token = getpass.getpass(f"Enter value for {key_name}: ")
                if not token:
                    console.print("[red]Error: Token cannot be empty.[/red]")
                    sys.exit(1)
                
                try:
                    keyring.set_password(cls.SERVICE_NAME, key_name, token)
                    console.print(f"[green]Successfully saved '{key_name}' to OS Keychain.[/green]")
                except keyring.errors.KeyringError:
                    console.print("[yellow]Warning: Could not save to OS Keychain (no backend available).[/yellow]")
                    
                return token
            except (KeyboardInterrupt, EOFError):
                console.print("\n[red]Cancelled by user. Exiting.[/red]")
                sys.exit(1)
        
        # 4. No TTY, but has display → Browser auth (the SILO way)
        if _has_display():
            try:
                from .interaction import prompt_via_browser
                token = prompt_via_browser(key_name)
                if token:
                    try:
                        keyring.set_password(cls.SERVICE_NAME, key_name, token)
                    except keyring.errors.KeyringError:
                        pass  # Token is still returned even if keychain save fails
                    return token
            except Exception:
                pass  # Browser flow failed, fall through to error

        # 5. Truly headless, no display, no TTY → structured error
        error = {
            "error": "SILO_AUTH_REQUIRED",
            "key": key_name,
            "message": f"The skill requires a secret '{key_name}' which is not configured.",
            "resolution": f"Set the environment variable '{key_name}' before running this command."
        }
        print(json.dumps(error))
        sys.exit(1)
