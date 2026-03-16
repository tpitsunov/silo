# Quickstart Guide

This guide will help you install the SILO framework, create your first AI skill, and run it.

## 1. Installation

You can install SILO using `pip` or `uv`. We recommend using `uv` for managing dependencies.

```bash
pip install silo-framework
# OR
uv tool install silo-framework
```

To verify installation, run:
```bash
silo --help
```
```text title="Output Simulation"
Usage: silo [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  auth     Manage secret keys in the local vault.
  init     Scaffold a new SILO skill.
  inspect  Show detailed skill info.
  install  Install a skill to the hub.
  mcp-run  Run the SILO MCP server.
  ps       List installed skills.
  run      Execute a tool from a skill.
  search   Search for tools semantically.
```

## 2. Generating Your First Skill

SILO provides a CLI tool to instantly scaffold new skills. Let's create a skill named `weather`.

```bash
silo init weather
```

This creates a new folder `weather` with a `skill.py` file. Open it in your editor:

```python title="weather/skill.py"
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "silo",
# ]
# ///

from silo import Skill, AgentResponse

skill = Skill(namespace="weather")

@skill.tool()
def get_forecast(city: str):
    """Returns the weather forecast for a city."""
    # In a real skill, you would call a weather API here.
    return AgentResponse(
        llm_text=f"The weather in {city} is sunny, 25°C.",
        raw_data={"city": city, "temp": 25, "condition": "sunny"}
    )
```

The `/// script` block tells `uv` exactly what dependencies this file needs.

## 3. Installing and Running

To make your skill available to the SILO hub, install it:

```bash
silo install ./weather
```

Now you can run it using the SILO runner:

```bash
silo run weather get_forecast --city "San Francisco"
```
```text title="Output Simulation"
⠋ Executing weather:get_forecast...
╭────────────────────────────── Execution Result ───────────────────────────────╮
│ The weather in San Francisco is sunny, 25°C.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## 4. How Secrets Work

If your skill requires an API key, use `silo.secrets.require("KEY_NAME")`. 

When you run the skill for the first time, SILO will:
1. Check your environment variables.
2. Check your OS Keychain.
3. If not found, it will open a browser window to securely ask you for the key and save it to your Keychain.

Next time you run the skill, it will load the key automatically from the Keychain.

You can see all tools and instructions for an installed skill using:
```bash
silo inspect weather
```
```text title="Output Simulation"
⠋ Inspecting weather...
╭─────────────────────────── Skill: weather (Instructions) ────────────────────────────╮
│ Use this tool when the user asks about weather or climate.                           │
╰──────────────────────────────────────────────────────────────────────────────────────╯
                                   Available Tools
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Tool Name    ┃ Description                                              ┃ Approvals ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ get_forecast │ Returns the weather forecast for a city.                  │   Auto    │
└──────────────┴──────────────────────────────────────────────────────────┴───────────┘
```

## 6. Finding Tools

If you can't remember the exact name of a tool or want to see what's available for a specific task, use the search command:

```bash
silo search "get weather"
```
```text title="Output Simulation"
⠋ Searching for 'get weather'...
                         Search results for 'get weather'
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool (ID)            ┃ Description                                                  ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ weather.get_forecast │ Returns the weather forecast for a city.                      │
└──────────────────────┴──────────────────────────────────────────────────────────────┘
```

SILO uses semantic matching to find the most relevant tools across all installed skills.

---

Now that you know the basics, explore:
* [Writing Skills](writing_skills.md): A deeper look at tools and response types.
* [Security & Secret Management](security-overview.md): How SILO protects your data.
