# Integration: Claude Desktop

Connecting SILO to Claude Desktop allows you to use all your installed skills directly within the Claude interface on macOS or Windows.

## 1. Locate Claude Config

Open the Claude Desktop configuration file:
- **macOS**: `~/Library/Application Support/AnthropicClaude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\AnthropicClaude\claude_desktop_config.json`

## 2. Add SILO as an MCP Server

Add a new entry to the `mcpServers` object. Replace `<PATH_TO_SILO>` with the absolute path to your `silo` executable (usually in your virtualenv or global path).

```json
{
  "mcpServers": {
    "silo-v2": {
      "command": "<PATH_TO_SILO>",
      "args": ["mcp", "run"]
    }
  }
}
```

## 3. Restart Claude

Completely quit and restart Claude Desktop. You should now see the `silo-v2` server connected in the settings.

## 4. Usage

Simply ask Claude to perform a task. 

- **Discovery**: Claude will automatically call `silo_search` if it doesn't find a direct tool match.
- **Execution**: Claude will call `silo_execute` to run the tools you discovered.

> **Example**: "Claude, search for a skill to check website metrics and then get the report for example.com."

---

**Next:** See how to use [Custom Orchestrators](custom.md).
