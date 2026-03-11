# 🏗️ SILO Framework

**S.I.L.O** (Secure. Isolated. Lightweight. Offloaded.) is a lightweight Python framework designed specifically for building **AI Skills**—tools that LLM agents can call safely, reliably, and with zero configuration headache.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Ready](https://img.shields.io/badge/MCP-Ready-green.svg)](https://modelcontextprotocol.io)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://github.com/tpitsunov/silo/tree/main/docs)

📖 **[Read the Documentation](https://tpitsunov.github.io/silo/)** (or browse [docs/index.md](docs/index.md)) for a quickstart guide, details on writing skills, security, and deploying as an MCP server.

---

## 🔥 Why SILO?

Most "AI Skills" today are just **unstructured text prompts** telling an agent to "be smart" and write code on the fly to solve a problem. This works for simple tasks, but falls apart when you need reliable, repeatable, and secure integrations.

### The Problem
*   **Token Leaks**: Passing API keys in prompts or CLI arguments is a massive security risk.
*   **Dependency Hell**: Each skill needs its own `.venv`, `requirements.txt`, and setup.
*   **LLM Hallucinations**: Agents struggle with unstructured text or unclear argument types.
*   **Complexity**: Writing a full MCP server or a robust CLI wrapper takes too much boilerplate.

### The SILO Solution
SILO is built on four core pillars:

- 🔒 **Secure**: Tokens or keys **never** reach the LLM context. In SILO, secrets live in your OS Keychain or Env, keeping them invisible to the model and the logs.
- 📦 **Isolated**: Each skill is a self-contained module. With `uv` (PEP 723) support, a single file can manage its own dependencies without polluting your global environment.
- 🪶 **Lightweight**: Skill instructions (SKILL.md) are minimalist and focused. A skill should solve one clearly defined task with maximum clarity.
- ⚡ **Offloaded**: Perform as much work as possible procedurally (in Python) rather than through the LLM. This saves tokens, reduces cognitive load on the agent, and ensures predictable, accurate results.

---

## 🚀 The SILO Workflow: How it Works

SILO transforms the development of AI tools into a streamlined 4-step process.

### 1. Scaffolding
Start with a single command to generate a compliant skill template.
```bash
silo init github_skill.py --secrets GITHUB_TOKEN
```
This creates a file with a **PEP 723** header, ensuring `uv` can run it with all necessary dependencies (including `silo-framework` itself) in a temporary, isolated environment.

### 2. Development (The Code)
Define your commands using standard Python functions and **Pydantic** models. SILO handles the rest—argument parsing, JSON serialization, and error handling.

```python
from silo import Skill, Secret, JSONResponse
from pydantic import BaseModel

app = Skill("github", description="Manage GitHub issues")

class Issue(BaseModel):
    title: str
    body: str

@app.command()
def create_issue(repo: str, detail: Issue):
    """Creates a new issue in a repository."""
    # This NEVER leaks to the LLM. 
    # It fetches from Keychain, Env, or prompts via browser.
    token = Secret.require("GITHUB_TOKEN") 
    
    # Procedural logic (Offloaded from LLM)
    return JSONResponse({"status": "created", "repo": repo, "issue": detail.title})

if __name__ == "__main__":
    app.run()
```

### 3. Verification (`silo test`)
Agents don't have a terminal (TTY). They don't have a display. They need clean, predictable output.
```bash
silo test github_skill.py create_issue --repo "user/repo" --detail '{"title": "Bug", "body": "Fixed"}'
```
`silo test` runs your skill in a simulated "headless agent" environment, verifying that:
*   The manifest generates correctly.
*   Authentication fallbacks trigger properly.
*   Output is valid JSON/Markdown.

### 4. Deployment & MCP Export
Want to use this skill in **Claude Desktop**? You don't need to rewrite a single line. Just change one method call:
```python
if __name__ == "__main__":
    # app.run()     <-- Standard CLI
    app.run_mcp()   <-- Instant MCP tool server!
```

---

## 🛠️ Advanced Features

### 🔐 Headless-Friendly Auth
When a skill needs a secret but there is no terminal (standard for agents), SILO:
1. Checks `os.environ`.
2. Checks the **OS Keychain** (macOS, Windows, Linux).
3. If missing and a display is detected, it opens a **local browser tab** with a secure dark-mode form for the user to input the token. The token is saved to the keychain and aldrig passed to the agent.

### 🩺 Environment Doctor
Not sure if your system is ready for S.I.L.O? 
```bash
silo doctor
```
Checks for Python version, `uv` presence, Keychain accessibility, and critical dependencies.

---

## 📜 License
MIT © Timur Pitsunov
