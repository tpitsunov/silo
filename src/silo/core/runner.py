import asyncio
import os
import json
from asyncio import subprocess
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from .hub import HubManager
from ..security.security import SecurityManager


class Runner:
    """
    Handles the execution of SILO skills in isolated environments using 'uv run'.
    """
    def __init__(self, hub: Optional[HubManager] = None):
        self.hub = hub or HubManager()
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._uv_path: Optional[str] = None

    @property
    def semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(10)
        return self._semaphore

    def _get_uv_path(self) -> str:
        if self._uv_path:
            return self._uv_path

        # 1. Try project venv
        # runner.py is in src/silo/core/runner.py, so we need 4 parents to reach the root
        project_root = Path(__file__).parent.parent.parent.parent.resolve()
        silo_vbin = project_root / ".venv" / "bin" / "uv"
        if silo_vbin.exists():
            self._uv_path = str(silo_vbin)
            return self._uv_path

        # 2. Try shutil.which
        uv_path = shutil.which("uv")
        if uv_path:
            self._uv_path = uv_path
            return self._uv_path

        # 3. Default to "uv"
        return "uv"

    def _resolve_entrypoint(self, skill_path: Path) -> Path:
        entrypoint = skill_path / "skill.py"
        if not entrypoint.exists():
            py_files = list(skill_path.glob("*.py"))
            if py_files:
                entrypoint = py_files[0]
            else:
                raise FileNotFoundError(f"No python entrypoint found in {skill_path}")
        return entrypoint

    def _resolve_secrets(self, namespace: str, user_secrets: Optional[Dict[str, str]]) -> Dict[str, str]:
        sm = SecurityManager()
        tracked = self.hub.get_tracked_secrets(namespace)
        hub_secrets = sm.load_credentials()
        secrets = user_secrets.copy() if user_secrets else {}
        for key in tracked:
            if key not in secrets:
                val = hub_secrets.get(key) or sm.get_desktop_secret(namespace, key)
                if isinstance(val, str):
                    secrets[key] = val
        return secrets

    def _prepare_env(self, namespace: str) -> Dict[str, str]:
        essential_vars = ["PATH", "HOME", "USER", "SHELL", "TMPDIR", "PYTHONPATH"]
        env = {k: os.environ[k] for k in essential_vars if k in os.environ}
        env["SILO_RUNNER"] = "1"
        env["SILO_NAMESPACE"] = namespace

        for k, v in os.environ.items():
            if k.startswith("SILO_") and k != "SILO_MASTER_KEY":
                env[k] = v
        return env

    def _get_execution_command(
        self,
        skill_path: Path,
        entrypoint: Path,
        tool_name: str,
        env: Dict[str, str]
    ) -> List[str]:
        venv_path = skill_path / ".venv"
        python_bin = venv_path / "bin" / "python"

        project_root = Path(__file__).parent.parent.parent.parent.resolve()
        src_root = project_root / "src"

        if python_bin.exists():
            pps = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = f"{src_root}:" + pps if pps else str(src_root)
            return [str(python_bin), str(entrypoint), tool_name]

        try:
            uv_bin = self._get_uv_path()
            base_cmd = [uv_bin, "run", "--no-project"]
            if (project_root / "pyproject.toml").exists():
                return base_cmd + ["--with", str(project_root), str(entrypoint), tool_name]
            return base_cmd + [str(entrypoint), tool_name]
        except (FileNotFoundError, RuntimeError, ValueError):
            return ["uv", "run", "--no-project", str(entrypoint), tool_name]

    def _add_tool_arguments(self, cmd: List[str], kwargs: Dict[str, Any]) -> List[str]:
        for key, value in kwargs.items():
            cmd.extend([f"--{key}", str(value)])
        return cmd

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

            entrypoint = self._resolve_entrypoint(skill_path)
            current_secrets = self._resolve_secrets(namespace, secrets)
            env = self._prepare_env(namespace)
            cmd = self._get_execution_command(skill_path, entrypoint, tool_name, env)

            # 4. Prepare STDIN payload
            cmd = self._add_tool_arguments(cmd, kwargs)

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
                    err_msg = f"Process exited with code {process.returncode}\n\n" \
                              f"[STDERR]\n{stderr_str}\n\n[STDOUT]\n{stdout_str}"
                    return {
                        "status": "error",
                        "error_message": err_msg,
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
        uv_bin = self._get_uv_path()

        try:
            # Create venv: uv venv .venv
            proc = await asyncio.create_subprocess_exec(
                uv_bin, "venv", ".venv", "--quiet",
                cwd=str(skill_path)
            )
            await proc.wait()

            # Find the SILO package root to install it (or its dependencies)

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
