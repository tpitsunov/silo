# CLI Reference

The SILO CLI provides a unified interface for managing the lifelong of AI Agent tools.

## General Commands

### `init <name>`
Scaffolds a new SILO skill directory.
```bash
silo init my-weather-skill
```

### `install <path>`
Installs a skill from a local directory or registry into the hub.
```bash
silo install ./my-weather-skill
```

### `ps`
Lists all installed skills, their disk usage (source and environment), and last used timestamp.
```bash
silo ps
```
```text title="Output Simulation"
                              Installed SILO Skills
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Namespace   ┃ Size (Src) ┃ Size (Env) ┃ Last Used                          ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ weather     │     1.2 KB │    14.5 MB │ 2024-03-13 18:30                   │
│ sysguard    │     1.9 KB │     0.0 B  │ 2024-03-13 12:15                   │
└─────────────┴────────────┴────────────┴────────────────────────────────────┘
```

### `run <namespace> <tool> [args...]`
Manually executes a tool from an installed skill. Key-value arguments can be passed as `key=value`.
```bash
silo run weather get_weather city=London
```
```text title="Output Simulation"
⠋ Executing weather:get_weather...
╭────────────────────────────── Execution Result ───────────────────────────────╮
│ The weather in London is currently 15°C and cloudy.                          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### `inspect <namespace>`
Displays detailed information about a skill, including its instructions and available tools.
```bash
silo inspect weather
```
```text title="Output Simulation"
⠋ Inspecting weather...
╭─────────────────────────── Skill: weather (Instructions) ────────────────────────────╮
│ Use this tool when the user asks about weather or climate.                           │
╰──────────────────────────────────────────────────────────────────────────────────────╯
                                   Available Tools
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Tool Name   ┃ Description                                              ┃ Approvals ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ get_weather │ Returns the current weather for a city.                  │   Auto    │
└─────────────┴──────────────────────────────────────────────────────────┴───────────┘
```

### `search <query>`
Performs a semantic (BM25) and exact search across all installed tools to find matches for a query.
```bash
silo search "get weather forecast"
```
```text title="Output Simulation"
⠋ Searching for 'get weather forecast'...
                         Search results for 'get weather forecast'
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool (ID)            ┃ Description                                                  ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ weather.get_weather  │ Returns the current weather for a city.                      │
└──────────────────────┴──────────────────────────────────────────────────────────────┘
```

## Security & Auth

### `auth set <key> <value>`
Encrypts and stores a secret key in the local SILO vault.
```bash
silo auth set OPENAI_API_KEY sk-...
```

### `mcp-run`
Starts the SILO Model Context Protocol (MCP) server. Use this to connect agents to your local hub.
```bash
silo mcp-run
```
