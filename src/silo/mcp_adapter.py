"""
MCP adapter for SILO skills.
Converts @app.command() functions into MCP tools using the official FastMCP SDK.
"""
import inspect
import functools

def create_mcp_server(app):
    """
    Takes a SILO Skill app and returns a FastMCP server with all
    registered commands exposed as MCP tools.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise ImportError(
            "MCP support requires the 'mcp' package. "
            "Install it with: pip install 'silo[mcp]' or pip install 'mcp[cli]'"
        )

    server = FastMCP(app.name)

    for cmd_name, func in app.commands.items():
        doc = inspect.getdoc(func) or f"Execute the '{cmd_name}' command."
        
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            from .responses import SiloResponse
            result = func(*args, **kwargs)
            if isinstance(result, SiloResponse):
                return result.to_mcp()
            return result

        # FastMCP's add_tool registers a callable as an MCP tool.
        # It introspects the function signature to build the input schema,
        # and natively supports Pydantic BaseModel parameters.
        server.add_tool(
            _wrapper,
            name=cmd_name,
            description=doc,
        )

    return server
