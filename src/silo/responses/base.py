
class SiloResponse:
    """Base class for all typed SILO responses."""

    def render(self) -> str:
        """Render the response as a string for CLI output."""
        raise NotImplementedError

    def to_mcp(self) -> str:
        """Render the response for MCP output (usually identical to CLI)."""
        return self.render()
