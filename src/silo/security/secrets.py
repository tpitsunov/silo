import json
import os
import sys
from typing import Dict, Optional, Any
from .security import SecurityManager
from ..core.hub import HubManager
from .vault import VaultManager

_STATE: Dict[str, Any] = {"initialized": False, "cache": {}}


def _get_combined_secrets() -> Dict[str, str]:
    """Helper to read secrets from STDIN."""
    combined = {}
    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read()
            if raw_input:
                combined.update(json.loads(raw_input))
        except (json.JSONDecodeError, IOError):
            pass
    return combined

def _try_vault_and_keychain(key_name: str) -> Optional[str]:
    """Helper to check Vault and Keychain/Hub for a secret."""
    # 2. Check HashiCorp Vault
    vm = VaultManager()
    if vm.is_configured():
        token = vm.get_secret(key_name)
        if token:
            return token

    # 3. Check Keychain/Hub
    sm, hm = SecurityManager(), HubManager()
    namespace = os.environ.get("SILO_NAMESPACE")
    if namespace:
        token = sm.get_desktop_secret(namespace, key_name) or sm.load_credentials().get(key_name)
        if token:
            hm.track_secret(namespace, key_name)
            return token
    return None

def _interactive_prompt(key_name: str) -> Optional[str]:
    """Helper for interactive browser prompt."""
    if os.environ.get("SILO_HEADLESS") == "1":
        return None
    try:
        from ..ui.interaction import prompt_via_browser
        token = prompt_via_browser(key_name)
        if token:
            sm, hm = SecurityManager(), HubManager()
            namespace = os.environ.get("SILO_NAMESPACE")
            if namespace:
                sm.set_desktop_secret(namespace, key_name, token)
                hm.track_secret(namespace, key_name)
            return token
    except (ImportError, RuntimeError, ValueError):
        pass
    return None

def require(key_name: str) -> str:
    """
    Requested a secret during runtime.
    The SILO runner injects these via STDIN as a JSON object.
    """
    if not _STATE["initialized"]:
        if not os.environ.get("SILO_RUNNER"):
            raise RuntimeError("require_secret() can only be used when running via 'silo run' or 'silo execute'")
        _STATE["cache"].update(_get_combined_secrets())
        _STATE["initialized"] = True

    cache = _STATE["cache"]
    if key_name in cache:
        return cache[key_name]

    # Try external sources
    token = _try_vault_and_keychain(key_name) or _interactive_prompt(key_name)
    if token:
        cache[key_name] = token
        return token

    raise KeyError(f"Secret '{key_name}' not provided to this skill environment.")
