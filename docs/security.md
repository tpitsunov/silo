# Security & Secret Management

SILO is designed with a "Security-First" philosophy, ensuring that sensitive data like API keys never leak into logs, environment history, or code repositories.

## Layered Secret Management

When a skill calls `silo.secrets.require("KEY_NAME")`, the framework searches for the secret in this specific order:

1.  **Environment Variables**: Primarily for CI/CD or advanced users.
2.  **OS Keychain**: The primary secure local storage. Keys are encrypted at rest by your operating system.
3.  **Interactive Browser Auth**: If the key is missing and the environment is not "headless", SILO opens a local browser window with a secure form to collect the secret.

## Keychain Persistence

Once a secret is provided via the browser, SILO automatically saves it to your system's Keychain (via the `keyring` library). This means:

*   You only enter your API key **once** per machine.
*   Secrets are stored separately from your project files.
*   Secrets are tied to a specific skill `namespace`.

## Sandbox Isolation

Every skill tool is executed in an isolated environment managed by `uv run`. 

*   **No Shared State**: Skills cannot accidentally interfere with each other's memory or variables.
*   **Dependency Pinning**: Skills use inline metadata (PEP 723) to ensure they always run with the correct library versions, preventing "dependency hell".

## Secret Tracking & Cleanup

SILO maintains a `meta` file for each skill to track which secret keys it has used. When you run `silo remove <namespace>`, the framework uses this tracking data to **completely wipe** the associated secrets from your system's Keychain, ensuring no "ghost" tokens are left behind.

## Headless Mode

For production environments (or when being called by another AI agent), you can enable **Headless Mode** by setting `SILO_HEADLESS=1`. In this mode:

*   Interactive browser prompts are disabled.
*   If a secret is missing, the skill immediately returns a structured JSON error instead of hanging.

## Approvals (Human-in-the-Loop)

Some actions (like deleting a database, committing code, sending an email) shouldn't be executed completely autonomously by an LLM.

SILO provides a `require_approval` flag on tools:
```python
@skill.tool(require_approval=True)
def delete_database(db_name: str):
    ...
```
This forces the runner to ask for human confirmation via the terminal or a browser before allowing the tool to execute.
