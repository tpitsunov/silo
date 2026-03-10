from .base import SiloResponse

class MarkdownResponse(SiloResponse):
    """A Markdown formatted text response."""

    def __init__(self, content: str):
        self.content = content

    def render(self) -> str:
        return self.content
