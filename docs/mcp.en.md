# MCP Deployment

The Model Context Protocol (MCP) by Anthropic is an open standard that allows developers to create secure servers that provide custom tools and integrations to LLM interfaces (like the Claude Desktop app).

SILO seamlessly supports exposing your skills as an MCP Server.

## How It Works

You don't need to rewrite any of your logic to be MCP-compatible.

If you built your CLI app using `app.run()`, changing it to an MCP Server just requires altering the entrypoint method:

```python
if __name__ == "__main__":
    # Changes from a standalone CLI tool to an MCP Server
    app.run_mcp()
```

## Configuring Claude Desktop

To add your skill to Claude Desktop, you just point the config to your standalone file via `uv`:

Open your Claude configuration file (e.g., `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS) and add the server:

```json
{
  "mcpServers": {
    "my_silo_skill": {
      "command": "uv",
      "args": [
        "run",
        "/absolute/path/to/my_skill.py"
      ]
    }
  }
}
```

Because SILO uses PEP 723 to declare inline dependencies in the single file, Claude Desktop will automatically install `silo-framework` (and any other requirements in the script block) into a temporary isolated environment on boot, perfectly loading your tools.

When Claude calls your tool, standard SILO rules apply: missing tokens or required approvals will spawn local headless warnings, keeping you secure out of the box!
