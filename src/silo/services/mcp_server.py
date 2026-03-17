import asyncio
import json
from typing import List, Dict, Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from .search import SearchEngine
from ..core.runner import Runner
from ..core.hub import HubManager

class SiloMCPServer:
    """
    Exposes SILO functionality via Model Context Protocol (MCP).
    """
    def __init__(self):
        self.hub = HubManager()
        self.search_engine = SearchEngine(self.hub)
        self.runner = Runner(self.hub)
        self.server = Server("silo-v2")
        self._setup_tools()

    def _setup_tools(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="silo_search",
                    description="Search for SILO skills and tools based on a natural language query.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query (e.g., 'get website metrics')"
                            },
                            "limit": {"type": "integer", "default": 5}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="silo_execute",
                    description="Execute a specific SILO tool from a discovered skill.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string", "description": "The skill namespace"},
                            "tool_name": {"type": "string", "description": "The name of the tool within the skill"},
                            "arguments": {"type": "object", "description": "Arguments for the tool"}
                        },
                        "required": ["namespace", "tool_name", "arguments"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "silo_search":
                query = arguments.get("query", "")
                limit = arguments.get("limit", 5)
                results = await self.search_engine.search(query, limit=limit)

                if not results:
                    return [TextContent(type="text", text="No relevant SILO skills or tools found for your query.")]

                formatted_results = []
                for res in results:
                    formatted_results.append(
                        f"Skill: {res['namespace']}\n"
                        f"Tool: {res['tool_name']}\n"
                        f"Description: {res['description']}\n"
                        f"Instructions: {res['instructions'][:200]}..."
                    )

                return [TextContent(type="text", text="\n---\n".join(formatted_results))]

            if name == "silo_execute":
                ns = arguments.get("namespace", "")
                tool = arguments.get("tool_name", "")
                args = arguments.get("arguments", {})

                # In Phase 4, we should check if approval is required
                # For now, we'll delegate to the runner
                result = await self.runner.execute(ns, tool, args)

                if result.get("status") == "error":
                    err_msg = result.get('error_message') or result.get('stderr')
                    return [TextContent(type="text", text=f"Error executing {ns}:{tool}: {err_msg}")]

                # Format response for LLM
                llm_text = result.get("llm_text", json.dumps(result))
                return [TextContent(type="text", text=llm_text)]

            raise ValueError(f"Unknown tool: {name}")

    async def run(self):
        """Run the MCP server over STDIN/STDOUT."""
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

if __name__ == "__main__":
    server = SiloMCPServer()
    asyncio.run(server.run())
