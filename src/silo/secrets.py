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
            
        combined_secrets = {}
        
        # 1. Try to read from Env Var (Injected by Runner)
        env_secrets = os.environ.get("SILO_SECRETS_JSON")
        if env_secrets:
            try:
                combined_secrets.update(json.loads(env_secrets))
            except Exception:
                pass
        
        # 2. Try to read from STDIN (Primary injection via pipe)
        # Note: We only do this if it's not a TTY, to avoid hanging on interactive input
        if not sys.stdin.isatty():
            try:
                # We use a non-blocking or timed read if possible, but for SILO, 
                # the runner closes the pipe after sending.
                raw_input = sys.stdin.read()
                if raw_input:
                    combined_secrets.update(json.loads(raw_input))
            except Exception:
                pass

        _SECRETS_CACHE = combined_secrets

    if key_name not in _SECRETS_CACHE:
        # 3. Check Keychain (local persistent fallback)
        sm = SecurityManager()
        hm = HubManager()
        namespace = os.environ.get("SILO_NAMESPACE")
        
        if namespace:
            # Priority: Keychain (Skill-specific) > Hub File (Global)
            token = sm.get_desktop_secret(namespace, key_name)
            if not token:
                hub_secrets = sm.load_credentials()
                token = hub_secrets.get(key_name)

            if token:
                if _SECRETS_CACHE is not None:
                    # Cast to dict to avoid Pyre error
                    from typing import cast
                    cast(Dict[str, str], _SECRETS_CACHE)[key_name] = token
                # Ensure it's tracked if found in keychain/hub but not in meta
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
