# Tutorial: Your First Skill

This guide will walk you through creating, installing, and running a simple SILO skill that fetches a random quote from an API.

## 1. Initialize the Skill

Use the SILO CLI to scaffold a new project. We'll call it `quote-master`.

```bash
silo init quote-master
```

## 2. Define Your Tools

Open `quote-master/skill.py` and replace its content with the following:

```python
import requests
from silo import Skill, AgentResponse

skill = Skill(namespace="quotes")

@skill.tool(require_approval=False)
def get_random_quote():
    """Fetches a random inspirational quote."""
    # Using dummyjson.com as a reliable source
    response = requests.get("https://dummyjson.com/quotes/random")
    data = response.json()
    return AgentResponse(
        llm_text=f"'{data['quote']}' — {data['author']}",
        raw_data=data
    )

if __name__ == "__main__":
    skill.run()
```

## 3. Install the Skill

Tell the SILO Hub about your new skill. This registers the namespace and prepares the sandbox.

```bash
silo install ./quote-master
```

## 4. Run Manually

Test your tool directly from the terminal. Note how SILO uses the namespace you defined in the code.

```bash
silo run quotes get_random_quote
```
```text title="Output Simulation"
⠋ Executing quotes:get_random_quote...
╭────────────────────────────── Execution Result ───────────────────────────────╮
│ 'Life is 10% what happens to you and 90% how you react to it.' — Charles R.  │
│ Swindoll                                                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## 5. View in Hub

Check your installed skills to see `quotes` in the list, along with its disk usage.

```bash
silo ps
```
```text title="Output Simulation"
                              Installed SILO Skills
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Namespace   ┃ Size (Src) ┃ Size (Env) ┃ Last Used                          ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ quotes      │     2.1 KB │    42.1 MB │ 2024-03-13 18:45                   │
└─────────────┴────────────┴────────────┴────────────────────────────────────┘
```

## 6. Inspecting Tools

To see exactly what tools a skill provides and read its instructions, use:
```bash
silo inspect quotes
```
```text title="Output Simulation"
⠋ Inspecting quotes...
╭─────────────────────────── Skill: quotes (Instructions) ─────────────────────────────╮
│ Describe the philosophical purpose and usage of this skill here.                    │
│ The Agent will read this to understand how to use the tools.                        │
╰──────────────────────────────────────────────────────────────────────────────────────╯
                                   Available Tools
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Tool Name        ┃ Description                                          ┃ Approvals ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ get_random_quote │ Fetches a random inspirational quote.                │   Auto    │
└──────────────────┴──────────────────────────────────────────────────────┴───────────┘
```

---

**Next Step:** Learn how to handle [Secret API Keys](../guide/security.md).
