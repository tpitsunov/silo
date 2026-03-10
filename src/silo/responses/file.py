import json
from pathlib import Path
from .base import SiloResponse

class FileResponse(SiloResponse):
    """A file-based response."""

    def __init__(self, path: str):
        self.path = path

    def render(self) -> str:
        p = Path(self.path)
        if not p.exists():
            return json.dumps({"error": "File not found", "path": self.path})
        
        return json.dumps({
            "type": "file",
            "path": str(p.absolute()),
            "size": p.stat().st_size
        })
