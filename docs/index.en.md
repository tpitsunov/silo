# Introduction to SILO Framework

**S.I.L.O** (Secure. Isolated. Lightweight. Offloaded.) is a lightweight Python framework designed specifically for building **AI Skills**—tools that LLM agents can call safely, reliably, and with zero configuration headache.

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
- 🪶 **Lightweight**: Skill instructions (`SKILL.md`) are minimalist and focused. A skill should solve one clearly defined task with maximum clarity.
- ⚡ **Offloaded**: Perform as much work as possible procedurally (in Python) rather than through the LLM. This saves tokens, reduces cognitive load on the agent, and ensures predictable, accurate results.

---

## Requirements

- **Python 3.9+**
- **uv** (Recommended): [uv](https://github.com/astral-sh/uv) handles PEP 723 isolated execution, making SILO skills incredibly simple to run without managing virtual environments.

## Next Steps

Head over to the [Quickstart Guide](quickstart.md) to create your first skill!
