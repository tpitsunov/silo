import asyncio
import os
import sys
import json
from asyncio import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from .hub import HubManager
from .security import SecurityManager


class Runner:
    """
    Handles the execution of SILO skills in isolated environments using 'uv run'.
    """
    def __init__(self, hub: Optional[HubManager] = None):
        self.hub = hub or HubManager()
        self.semaphore = asyncio.Semaphore(10) # Default max_workers=10

    async def execute(
        self, 
        namespace: str, 
        tool_name: str, 
        kwargs: Dict[str, Any],
        secrets: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executes a specific tool within a skill namespace.
        """
        async with self.semaphore:
            skill_path = self.hub.get_skill_path(namespace)
            if not skill_path.exists():
                raise FileNotFoundError(f"Skill '{namespace}' not found in hub.")

            entrypoint = skill_path / "skill.py"
            if not entrypoint.exists():
                # Check for other entrypoints if it's a legacy skill
                py_files = list(skill_path.glob("*.py"))
                if py_files:
                    entrypoint = py_files[0]
                else:
                    raise FileNotFoundError(f"No python entrypoint found in {skill_path}")

            # 1. Load tracked secrets from keychain AND encrypted hub file
            sm = SecurityManager()
            tracked = self.hub.get_tracked_secrets(namespace)
            
            # Load global secrets from encrypted file
            hub_secrets = sm.load_credentials()
            
            if secrets is None:
                current_secrets_dict: Dict[str, str] = {}
            else:
                from typing import cast
                current_secrets_dict = cast(Dict[str, str], secrets)
            
            for key in tracked:
                if key not in current_secrets_dict:
                    # Priority: Hub file > Keychain
                    val = hub_secrets.get(key)
                    if not val:
                        val = sm.get_desktop_secret(namespace, key)
                    
                    if isinstance(val, str):
                        current_secrets_dict[key] = str(val)
            current_secrets = current_secrets_dict
            
            # 2. Prepare environment variables (Whitelist only)
            essential_vars = ["PATH", "HOME", "USER", "SHELL", "TMPDIR", "PYTHONPATH"]
            env = {k: os.environ[k] for k in essential_vars if k in os.environ}
            env["SILO_RUNNER"] = "1"
            env["SILO_NAMESPACE"] = namespace
            
            # Pass through any SILO_ prefixed vars
            for k, v in os.environ.items():
                if k.startswith("SILO_") and k != "SILO_MASTER_KEY":
                    env[k] = v

            if current_secrets:
                # We no longer pass secrets via environment variables to prevent leakage
                # they are strictly passed via STDIN pipe.
                pass

            # 3. Determine the execution command
            # Preference: Local Hub .venv > Local Project .venv > Global uv
            venv_path = skill_path / ".venv"
            python_bin = venv_path / "bin" / "python"
            
            # Find the SILO package roots
            project_root = Path(__file__).parent.parent.parent.resolve()
            src_root = project_root / "src"
            
            if python_bin.exists():
                # Direct execution via the local venv's python
                cmd = [str(python_bin), str(entrypoint), tool_name]
                # Inject SILO source into PYTHONPATH so it's available in the venv
                # We point to 'src' so 'import silo' finds 'src/silo'
                env["PYTHONPATH"] = str(src_root) + (":" + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
            else:
                # Fallback to uv run (PEP 723 global cache mode)
                try:
                    pyproject = project_root / "pyproject.toml"
                    base_cmd = ["uv", "run", "--no-project"]
                    if pyproject.exists():
                        # We use '--with project_root' so uv installs the local silo-framework
                        cmd = base_cmd + ["--with", str(project_root), str(entrypoint), tool_name]
                    else:
                        cmd = base_cmd + [str(entrypoint), tool_name]
                except Exception:
                    cmd = ["uv", "run", "--no-project", str(entrypoint), tool_name]

            # 4. Add tool arguments
            for key, value in kwargs.items():
                cmd.extend([f"--{key}", str(value)])

            # 5. Execute
            try:
                # We use a limited buffer size for pipe reading to prevent memory exhaustion
                # Note: create_subprocess_exec 'limit' parameter is for the stream reader
                MAX_OUTPUT_BYTES = 10 * 1024 * 1024 # 10MB limit
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    env=env,
                    cwd=str(skill_path),
                    limit=MAX_OUTPUT_BYTES
                )

                # Inject secrets via STDIN as JSON (Primary method)
                input_data = b""
                if current_secrets:
                    input_data = json.dumps(current_secrets).encode()
                
                stdout, stderr = await process.communicate(input=input_data)
                
                stdout_str = stdout.decode().strip()
                stderr_str = stderr.decode().strip()
                
                # We attempt to parse stdout as JSON regardless of return code.
                tool_output = None
                try:
                    tool_output = json.loads(stdout_str)
                except json.JSONDecodeError:
                    pass

                if process.returncode != 0:
                    # If it's valid JSON error from the skill, return it directly
                    if tool_output and isinstance(tool_output, dict) and tool_output.get("status") == "error":
                        return tool_output
                    
                    # Otherwise, return a generic process error
                    return {
                        "status": "error", 
                        "error_message": f"Process exited with code {process.returncode}\n\n[STDERR]\n{stderr_str}\n\n[STDOUT]\n{stdout_str}",
                        "stderr": stderr_str,
                        "stdout": stdout_str,
                        "exit_code": process.returncode
                    }
                
                if tool_output and isinstance(tool_output, dict):
                    # If the tool output already has 'status', 'instructions' or 'tools',
                    # we return it directly to avoid redundant wrapping.
                    if any(k in tool_output for k in ["status", "instructions", "tools"]):
                        # Ensure 'status' is present if missing
                        if "status" not in tool_output:
                            tool_output["status"] = "success"
                        return tool_output
                
                return {"status": "success", "llm_text": stdout_str, "raw_data": tool_output}

            except Exception as e:
                return {"status": "error", "error_message": str(e)}
        
        # Fallback return (should not be reached due to semaphore context)
        return {"status": "error", "error_message": "Execution escaped unexpectedly."}

    async def precache(self, namespace: str):
        """
        Creates/Syncs a local .venv for a skill in the hub using 'uv'.
        """
        skill_path = self.hub.get_skill_path(namespace)
        if not skill_path.exists():
            return False

        entrypoint = skill_path / "skill.py"
        if not entrypoint.exists():
            return False

        # 1. Create a local venv inside the skill directory
        # We assume 'uv' is available in the path or we use the project's one
        # To be safe, we use 'uv' command. In the user's env it might be direct.
        # We can try to use relative path if we are in the silo repo.
        uv_bin = "uv"
        silo_vbin = Path(__file__).parent.parent.parent / ".venv" / "bin" / "uv"
        if silo_vbin.exists():
            uv_bin = str(silo_vbin)

        try:
            # Create venv: uv venv .venv
            proc = await asyncio.create_subprocess_exec(
                uv_bin, "venv", ".venv", "--quiet",
                cwd=str(skill_path)
            )
            await proc.wait()
            
            # Find the SILO package root to install it (or its dependencies)
            silo_pkg_root = Path(__file__).parent.parent.parent.resolve()
            
            # Install dependencies: uv pip install <entrypoint> + core dependencies
            # We install core SILO dependencies so 'import silo' (via PYTHONPATH injection) works.
            # In a real release, we would 'uv pip install silo'.
            core_deps = ["pydantic", "rich", "typer", "cryptography", "rank-bm25", "keyring", "hvac"]
            
            proc = await asyncio.create_subprocess_exec(
                uv_bin, "pip", "install", "-r", str(entrypoint), *core_deps, "--quiet",
                cwd=str(skill_path),
                env={**os.environ, "VIRTUAL_ENV": str(skill_path / ".venv")}
            )
            await proc.wait()
            return proc.returncode == 0
        except Exception:
            return False
    
    async def run_manual(self, namespace: str, tool_name: str, args: List[str]) -> Dict[str, Any]:
        """
        Manually run a skill with raw string arguments.
        """
        # We need to map raw args to a generic 'args' kwarg for the tool
        return await self.execute(namespace, tool_name, {"args": " ".join(args)})
