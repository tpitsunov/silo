import os
import json
import tarfile
import tempfile
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from .security import SecurityManager

from .security import SecurityManager

REMOTES_FILE = Path.home() / ".silo" / "remotes.json"
DEFAULT_REGISTRY = "https://registry.silo.sh"

class RegistryManager:
    """
    Handles communication with multiple remote SILO Registries.
    """
    def __init__(self):
        self._ensure_config_dir()
        self.remotes = self._load_remotes()
        self.sm = SecurityManager()

    def _ensure_config_dir(self):
        REMOTES_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_remotes(self) -> Dict[str, str]:
        if REMOTES_FILE.exists():
            try:
                with open(REMOTES_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"default": DEFAULT_REGISTRY}

    def _save_remotes(self):
        with open(REMOTES_FILE, "w") as f:
            json.dump(self.remotes, f, indent=2)

    def add_remote(self, name: str, url: str):
        """Add a new named remote registry."""
        self.remotes[name] = url.rstrip("/")
        self._save_remotes()

    def remove_remote(self, name: str):
        """Remove a named remote registry."""
        if name in self.remotes:
            del self.remotes[name]
            self._save_remotes()

    def get_url(self, name: str = "default") -> str:
        """Get the URL for a named remote."""
        return self.remotes.get(name, DEFAULT_REGISTRY)

    def get_token(self, remote_name: str = "default") -> Optional[str]:
        """Retrieve the registry API token for a specific remote from secure storage."""
        return self.sm.get_desktop_secret(f"registry:{remote_name}", "api_token")

    def set_token(self, token: str, remote_name: str = "default"):
        """Save the registry API token for a specific remote to secure storage."""
        self.sm.set_desktop_secret(f"registry:{remote_name}", "api_token", token)

    def _get_headers(self, remote_name: str = "default") -> Dict[str, str]:
        token = self.get_token(remote_name)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def search(self, query: str, remote_name: str = "default") -> List[Dict[str, Any]]:
        """Search for skills in a specific remote registry."""
        url = self.get_url(remote_name)
        try:
            response = requests.get(
                f"{url}/v1/search",
                params={"query": query},
                headers=self._get_headers(remote_name),
                timeout=10
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            for res in results:
                res["remote"] = remote_name
            return results
        except Exception:
            return []

    def get_skill_metadata(self, namespace: str, remote_name: str = "default") -> Optional[Dict[str, Any]]:
        """Fetch metadata for a specific skill from a specific registry."""
        url = self.get_url(remote_name)
        try:
            response = requests.get(
                f"{url}/v1/skills/{namespace}",
                headers=self._get_headers(remote_name),
                timeout=10
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def download_skill(self, namespace: str, target_path: Path, remote_name: str = "default") -> bool:
        """Download and extract a skill package from a specific registry with security checks."""
        metadata = self.get_skill_metadata(namespace, remote_name)
        if not metadata or "package_url" not in metadata:
            return False

        try:
            response = requests.get(metadata["package_url"], stream=True, timeout=30)
            response.raise_for_status()

            import hashlib
            sha256 = hashlib.sha256()

            with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False, mode="wb") as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                    sha256.update(chunk)
                tmp_name = tmp.name

            # Verify checksum if available in metadata
            expected_hash = metadata.get("checksum")
            if expected_hash and sha256.hexdigest() != expected_hash:
                os.unlink(tmp_name)
                return False

            def is_within_directory(directory, target):
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
                prefix = os.path.commonprefix([abs_directory, abs_target])
                return prefix == abs_directory

            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
                tar.extractall(path, members, numeric_owner=numeric_owner)

            with tarfile.open(tmp_name, "r:gz") as tar:
                safe_extract(tar, path=target_path)
            
            os.unlink(tmp_name)
            return True
        except Exception:
            return False

    def publish(self, skill_path: Path, metadata: Dict[str, Any], remote_name: str = "default") -> Dict[str, Any]:
        """Package and publish a skill to a specific registry."""
        token = self.get_token(remote_name)
        if not token:
            return {"status": "error", "message": f"Authentication required for remote '{remote_name}'. Use 'silo auth login --remote {remote_name}'."}

        # Create tarball
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            with tarfile.open(fileobj=tmp, mode="w:gz") as tar:
                # Get files to include (excluding .siloignore and envs)
                ignore_file = skill_path / ".siloignore"
                ignore_list = [".venv", "__pycache__", ".git", ".DS_Store"]
                if ignore_file.exists():
                    ignore_list.extend([l.strip() for l in ignore_file.read_text().splitlines() if l.strip()])

                def filter_files(tarinfo):
                    if tarinfo.name in ignore_list or any(tarinfo.name.startswith(i + "/") for i in ignore_list):
                        return None
                    return tarinfo

                tar.add(skill_path, arcname=".", filter=filter_files)
            tmp_name = tmp.name

        try:
            with open(tmp_name, "rb") as f:
                files = {"package": f}
                data = {"metadata": json.dumps(metadata)}
                headers = {"Authorization": f"Bearer {token}"}
                
                url = self.get_url(remote_name)
                response = requests.post(
                    f"{url}/v1/publish",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"status": "error", "message": f"Publishing failed: {str(e)}"}
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
