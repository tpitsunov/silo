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
        meta = app.command_metadata.get(cmd_name, {})
        
        # We need a closure that captures current cmd_name and func
        def create_wrapper(c_name, f, m):
            @functools.wraps(f)
            def _wrapper(*args, **kwargs):
                from .responses import SiloResponse
                
                # Check for approval if required
                if m.get("require_approval"):
                    # For MCP, args usually come in as kwargs
                    if not app._request_approval(c_name, kwargs):
                        return "Action rejected by user."
                
                result = f(*args, **kwargs)
                if isinstance(result, SiloResponse):
                    return result.to_mcp()
                return result
            return _wrapper

        # FastMCP's add_tool registers a callable as an MCP tool.
        server.add_tool(
            create_wrapper(cmd_name, func, meta),
            name=cmd_name,
            description=doc,
        )

    return server
