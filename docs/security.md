# Security and Approvals

Security is a primary focus of SILO. If you put an API Key into a standard prompt or context window, the model could easily hallucinate and send it in a network request, leak it in a response, or write it to a file.

SILO keeps secrets in a safe "vault" that the LLM never touches.

## The `Secret` Class

Use `Secret.require()` to fetch credentials safely and procedurally in Python, instead of relying on the LLM to provide them.

```python
from silo import Skill, Secret, JSONResponse

app = Skill("github_skill")

@app.command()
def get_profile():
    token = Secret.require("GITHUB_TOKEN")
    # Procedural logic here...
    return JSONResponse({"status": "success"})
```

### How `Secret.require` resolves keys:
When you run a command requiring a token:

1. **Environment Variables**: SILO checks `os.environ` first. If present, it uses it.
2. **OS Keychain**: SILO securely queries the operating system's native keychain (Keychain Access on macOS, Credential Locker on Windows, Secret Service on Linux). This is secure on-disk storage.
3. **Interactive Fallback**: If neither are found:
    - If SILO detects a display environment (i.e. not headless), it automatically launches a slick, dark-mode browser tab. 
    - You paste your API key into this local, private HTML form.
    - SILO saves the token strictly to the OS Keychain and resumes execution. *The token never prints to the console or log.*
4. **Headless Rejection**: If SILO is running in a purely CI/headless environment without the token (such as being executed by an LLM in the background), it throws a structured JSON error `{"error": "SILO_AUTH_REQUIRED"}` which an agent can understand and bubble up to the user.

## Approvals (Human-in-the-Loop)

Some actions (like deleting a database, committing code, sending an email) shouldn't be executed completely autonomously by an LLM.

SILO provides a `require_approval` flag on commands.

```python
from silo import Skill

app = Skill("db_manager")

@app.command(require_approval=True)
def drop_table(table_name: str):
    """Deletes a database table."""
    return {"status": "table dropped"}
```

When an LLM agent executes this command, it halts before the function runs. Like the Secret feature:
1. SILO checks if there's a TTY. If so, it asks via a clean textual `[y/N]` prompt in the terminal.
2. If there's no TTY but there is a display, it opens a secure browser confirmation window showing the exact command and arguments that the agent is trying to execute, demanding explicit human consent.
3. If the user rejects, or if the system is fully headless, the agent receives an error: `{"error": "SILO_APPROVAL_REQUIRED"}`.
