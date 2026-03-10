# 🏗️ SILO Framework

**S.I.L.O** (Secure. Isolated. Logical. Open.) is a lightweight Python framework designed specifically for building **AI Skills**—tools that LLM agents can call safely and reliably.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Ready](https://img.shields.io/badge/MCP-Ready-green.svg)](https://modelcontextprotocol.io)

---

## 🔥 Why SILO?

Most AI tools today are just loose Python scripts. SILO turns them into professional-grade skills with four core pillars:

- 🔒 **Secure**: Secrets (API keys) never leak to the LLM. They live in your OS Keychain or Env, with a headless-friendly browser auth fallback.
- 📦 **Isolated**: Full support for `uv` (PEP 723), allowing skills to be single-file scripts with pinned, auto-installing dependencies.
- 🏗️ **Logical**: Typed inputs (Pydantic) and structured outputs (JSON/Markdown) ensure agents don't hallucinate.
- 🌍 **Open**: Export any SILO skill to the **Model Context Protocol (MCP)** with one line of code.

---

## ⚡ Quickstart

### 1. Install
```bash
pip install silo-framework
# or with MCP support
pip install "silo-framework[mcp]"
```

### 2. Scaffold a Skill
```bash
silo init my_github_skill.py --secrets GITHUB_TOKEN
```

### 3. Define a Command
```python
from silo import Skill, Secret, JSONResponse

app = Skill("github", description="Manage GitHub issues")

@app.command()
def create_issue(repo: str, title: str, body: str):
    """Creates a new issue in a repository."""
    token = Secret.require("GITHUB_TOKEN")
    # ... call GitHub API ...
    return JSONResponse({"status": "created", "url": "..."})

if __name__ == "__main__":
    app.run()
```

---

## 🛠️ Key Features

### 🔐 Secure Secret Management
SILO never passes tokens to the agent. When `Secret.require("KEY")` is called:
1. It checks environment variables (for CI/CD).
2. It looks in the **OS Keychain** (macOS/Windows/Linux).
3. If missing, it opens a **local browser tab** to safely prompt the user.

### 🧩 MCP Native
Turn any skill into a Claude Desktop tool:
```python
if __name__ == "__main__":
    # app.run()     <-- CLI Mode
    app.run_mcp()   <-- MCP Mode!
```

### 🩺 Diagnostic Doctor
Is your environment ready?
```bash
silo doctor
```

### 🔍 Automated Testing for Agents
Ensure your skill won't break if called by an agent without a TTY:
```bash
silo test my_skill.py create_issue --repo "user/repo" --title "test"
```

---

## 📜 License
MIT © SILO Team
