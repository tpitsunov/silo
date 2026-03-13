# Integration: Custom Orchestrators

While SILO works great with Claude Desktop via MCP, it's also designed to be used programmatically in your own Python-based AI agents.

## 1. Using the `Runner` Directly

The `Runner` class in the `silo.runner` module is the programmatic way to execute skills from your code.

```python
from silo.hub import HubManager
from silo.runner import Runner

hub = HubManager()
runner = Runner(hub)

async def main():
    # Execute a tool
    result = await runner.execute(
        namespace="quotes",
        tool="get_random_quote",
        kwargs={}
    )
    
    print(result["llm_text"])

asyncio.run(main())
```

## 2. Using the `SearchEngine`

You can integrate SILO's dynamic discovery into your agent's reasoning loop.

```python
from silo.search import SearchEngine

search = SearchEngine()

async def discover_tools(query: str):
    results = await search.search(query, limit=3)
    for res in results:
        print(f"Found {res['full_id']}: {res['description']}")
```

## 3. Connecting to LangChain / LlamaIndex

Since SILO provides a standard MCP interface, you can use existing MCP adapters for framework like LangChain.

```python
# Pseudo-code example
from langchain_mcp import MCPServerTool

s_tool = MCPServerTool(
    command="silo",
    args=["mcp-run"]
)
agent.add_tool(s_tool)
```

---

**Next:** Check out the full [CLI Reference](../reference/cli.md).
