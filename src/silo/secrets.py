import json
import os
import sys
from typing import Dict, Optional
from pathlib import Path
from .security import SecurityManager
from .hub import HubManager

_SECRETS_CACHE: Optional[Dict[str, str]] = None


def require(key_name: str) -> str:
    """
    Requested a secret during runtime. 
    The SILO runner injects these via STDIN as a JSON object.
    """
    global _SECRETS_CACHE
    
    if _SECRETS_CACHE is None:
        # Check if we're running in a SILO runner environment
        if not os.environ.get("SILO_RUNNER"):
            raise RuntimeError("silo.secrets.require() can only be used when running via 'silo run' or 'silo execute'")
            
        # Try to read from STDIN (injected by the runner)
        try:
            raw_input = sys.stdin.read()
            if raw_input:
                _SECRETS_CACHE = json.loads(raw_input)
            else:
                _SECRETS_CACHE = {}
        except Exception as e:
            # Fallback to env var for older/legacy support
            env_secrets = os.environ.get("SILO_SECRETS_JSON")
            if env_secrets:
                _SECRETS_CACHE = json.loads(env_secrets)
            else:
                _SECRETS_CACHE = {}

    if key_name not in _SECRETS_CACHE:
        # 3. Check Keychain (local persistent fallback)
        sm = SecurityManager()
        hm = HubManager()
        namespace = os.environ.get("SILO_NAMESPACE")
        
        if namespace:
            token = sm.get_desktop_secret(namespace, key_name)
            if token:
                if _SECRETS_CACHE is not None:
                    # Cast to dict to avoid Pyre error
                    from typing import cast
                    cast(Dict[str, str], _SECRETS_CACHE)[key_name] = token
                # Ensure it's tracked if found in keychain but not in meta
                hm.track_secret(namespace, key_name)
                return token

        # 4. Interactive fallback (Premium feature)
        if os.environ.get("SILO_HEADLESS") != "1":
            try:
                from .interaction import prompt_via_browser
                token = prompt_via_browser(key_name)
                if token:
                    cache = _SECRETS_CACHE
                    cache[key_name] = token
                    
                    # Persist the secret to keychain and track it
                    sm = SecurityManager()
                    hm = HubManager()
                    
                    # Use namespace from environment
                    namespace = os.environ.get("SILO_NAMESPACE")
                    if namespace:
                        sm.set_desktop_secret(namespace, key_name, token)
                        hm.track_secret(namespace, key_name)
                    
                    return token
            except Exception:
                pass

        raise KeyError(f"Secret '{key_name}' not provided to this skill environment.")
        
    return _SECRETS_CACHE[key_name]
