import json
from typing import Any, Dict
from .base import SiloResponse

class JSONResponse(SiloResponse):
    """A structured JSON response."""

    def __init__(self, data: Dict[str, Any], indent: int = 2):
        self.data = data
        self.indent = indent

    def render(self) -> str:
        return json.dumps(self.data, indent=self.indent)
