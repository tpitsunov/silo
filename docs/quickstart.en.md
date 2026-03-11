# Quickstart Guide

This guide will help you install the SILO framework, create your first AI skill, test it, and run it.

## 1. Installation

You can install SILO using `pip` or `uv`. We highly recommend having `uv` installed, as SILO skills are designed to run as standalone scripts with inline dependencies (PEP 723).

```bash
pip install -e .
```
*(assuming you are installing the framework locally for now)*

To check if your environment is ready for SILO, run the doctor command:

```bash
silo doctor
```

This will verify your Python version, check for `uv`, and test if the OS Keychain is working.

## 2. Generating Your First Skill

SILO provides a CLI tool to instantly scaffold new skills. Let's create a skill that interacts with GitHub. We know it will need a `GITHUB_TOKEN`.

```bash
silo init github_skill.py --secrets GITHUB_TOKEN
```

This creates a new file called `github_skill.py`. Open it in your editor:

```python title="github_skill.py"
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "silo",
# ]
# ///

from typing import Optional
from pydantic import BaseModel, Field
from silo import Skill, Secret, JSONResponse

app = Skill(name="My Skill", description="A new SILO skill.")

@app.command()
def do_something(param: str):
    """Does something awesome."""
    token = Secret.require("GITHUB_TOKEN")
    return JSONResponse({"status": "success", "param": param})

if __name__ == "__main__":
    app.run()
```

Notice the top section: The `/// script` block tells `uv` exactly what dependencies this file needs to run (in this case, just `silo`). You can run this single file anywhere on your machine without manually creating a virtual environment.

## 3. Running the Skill

You can test the skill standard execution via `uv`:

```bash
uv run github_skill.py do_something --param hello
```

**What happens?**
Since your script requires `GITHUB_TOKEN`, SILO will look for it in the environment variables or the OS Keychain.
If it doesn't find it, and you're running it interactively (not headless), SILO will open a local browser window, prompting you to securely enter the token. It will then save the token to your system's Keychain for future use.

## 4. Testing for Agents (`silo test`)

An LLM agent operates in a "headless" environment (no TTY, no browser). It is critical that your skill behaves predictably and doesn't hang waiting for user input that the agent can't provide.

Use `silo test` to run your skill in simulated "headless" mode:

```bash
silo test github_skill.py do_something --param agent_test
```

`silo test` verifies that:
1. The script can automatically generate its Markdown manifest (`SKILL.md`).
2. Authentication fallbacks (returning clear JSON errors when secrets are missing) trigger properly instead of hanging.
3. The output is clean, valid JSON or Markdown that the LLM can parse easily.
