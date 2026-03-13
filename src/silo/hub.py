import os
import shutil
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

SILO_DIR = Path.home() / ".silo"
HUB_DIR = SILO_DIR / "hub"
SKILLS_DIR = HUB_DIR / "skills"
VENV_DIR = HUB_DIR / "venvs"

class HubManager:
    def __init__(self):
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure all required directories exist."""
        for d in [SILO_DIR, HUB_DIR, SKILLS_DIR, VENV_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def get_skill_path(self, namespace: str) -> Path:
        """Return the path to a skill directory."""
        return SKILLS_DIR / namespace

    def is_installed(self, namespace: str) -> bool:
        """Check if a skill is installed."""
        return self.get_skill_path(namespace).exists()

    def install_local(self, source_path: Path, namespace: str):
        """Install a skill from a local path."""
        target = self.get_skill_path(namespace)
        if target.exists():
            shutil.rmtree(target)
        
        if source_path.is_dir():
            shutil.copytree(source_path, target)
        else:
            target.mkdir(parents=True)
            shutil.copy2(source_path, target / "skill.py")
        
        self.update_lru(namespace)

    def remove(self, namespace: str):
        """Remove a skill, its associated venv, and its secrets."""
        # 1. Clean up secrets from keychain
        from .security import SecurityManager
        sm = SecurityManager()
        tracked_secrets = self.get_tracked_secrets(namespace)
        for key in tracked_secrets:
            sm.delete_desktop_secret(namespace, key)

        # 2. Delete skill directory
        skill_path = self.get_skill_path(namespace)
        if skill_path.exists():
            shutil.rmtree(skill_path)
        
        # 3. Handle venv removal
        venv_path = VENV_DIR / namespace
        if venv_path.exists():
            shutil.rmtree(venv_path)

    def list_skills(self) -> List[str]:
        """List all installed skills."""
        if not SKILLS_DIR.exists():
            return []
        return [d.name for d in SKILLS_DIR.iterdir() if d.is_dir()]

    def update_lru(self, namespace: str):
        """Update the Last Recently Used timestamp for a skill."""
        meta_path = self.get_skill_path(namespace) / ".silo_meta.json"
        meta: Dict[str, Any] = {}
        if meta_path.exists():
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
            except Exception:
                pass
        
        from typing import cast
        if not isinstance(meta, dict):
            meta_dict = cast(Dict[str, Any], {})
        else:
            meta_dict = cast(Dict[str, Any], meta)
            
        meta_dict["last_used"] = datetime.now().isoformat()
        with open(meta_path, "w") as f:
            json.dump(meta_dict, f)

    def get_last_used(self, namespace: str) -> Optional[datetime]:
        """Get the last used timestamp for a skill."""
        meta_path = self.get_skill_path(namespace) / ".silo_meta.json"
        if not meta_path.exists():
            return None
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
                return datetime.fromisoformat(meta["last_used"])
        except Exception:
            return None

    def track_secret(self, namespace: str, key: str):
        """Record that a skill uses a specific secret key."""
        meta_path = self.get_skill_path(namespace) / ".silo_meta.json"
        
        meta: Dict[str, Any] = {}
        if meta_path.exists():
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
            except Exception:
                pass
        
        from typing import cast
        if not isinstance(meta, dict):
            meta_dict = cast(Dict[str, Any], {})
        else:
            meta_dict = cast(Dict[str, Any], meta)
            
        secrets = meta_dict.get("secrets", [])
        if key not in secrets:
            secrets.append(key)
            meta_dict["secrets"] = secrets
            
            # Ensure folder exists
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(meta_path, "w") as f:
                meta_to_save: Dict[str, Any] = meta # type: ignore
                json.dump(meta_to_save, f)

    def get_tracked_secrets(self, namespace: str) -> List[str]:
        """Get the list of secret keys used by a skill."""
        meta_path = self.get_skill_path(namespace) / ".silo_meta.json"
        if not meta_path.exists():
            return []
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
                return meta.get("secrets", [])
        except Exception:
            return []

    def save_metadata(self, namespace: str, metadata: Dict[str, Any]):
        """Save full skill metadata (tools, instructions, etc.) for search."""
        path = self.get_skill_path(namespace)
        meta_path = path / ".silo_meta.json"
        
        existing: Dict[str, Any] = {}
        if meta_path.exists():
            try:
                with open(meta_path, "r") as f:
                    existing = json.load(f)
            except Exception:
                pass
        
        # Merge new metadata into existing (to preserve secrets/last_used if not in 'metadata')
        existing.update(metadata)
        
        with open(meta_path, "w") as f:
            json.dump(existing, f)

    def get_disk_usage(self, namespace: str) -> Dict[str, int]:
        """Return disk usage for skill source and its associated venv in bytes."""
        def get_dir_size(path: Path, exclude: Optional[str] = None) -> int:
            total = 0
            if not path.exists():
                return 0
            try:
                for entry in os.scandir(path):
                    if exclude and entry.name == exclude:
                        continue
                    if entry.is_file():
                        total += entry.stat().st_size
                    elif entry.is_dir():
                        total += get_dir_size(Path(entry.path), exclude)
            except (PermissionError, OSError):
                pass
            return total

        skill_path = self.get_skill_path(namespace)
        venv_path = VENV_DIR / namespace
        
        # Local venv discovery
        local_venv = skill_path / ".venv"
        
        return {
            "source": get_dir_size(skill_path, exclude=".venv"),
            "venv": get_dir_size(venv_path) + get_dir_size(local_venv)
        }
