import json
from typing import Any, Dict
from .base import SiloResponse

class ErrorResponse(SiloResponse):
    """A structured error response."""

    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}

    def render(self) -> str:
        return json.dumps({
            "error": self.message,
            "details": self.details
        }, indent=2)
