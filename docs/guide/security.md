# Deep Dive: Security & Sandboxing

SILO V2 is designed as a "Secure Agentic OS." This means that unlike traditional scripts, tools executed via SILO never have direct access to your global environment variables, sensitive files (unless authorized), or the parent process.

## 1. The `uv run` Sandbox

Every time an Agent calls a SILO tool, the framework spawns a fresh process using:
```bash
uv run <skill_script>.py <tool_name> --args...
```

- **Isolation**: Each skill maintains its own `.venv` and dependency list.
- **Reproducibility**: `uv` ensures the tool runs in the exact same environment every time.
- **Cleanup**: Transient data within the sandbox is not persisted unless explicitly saved to a mapped volume.

## 2. Secure Secret Injection

This is the most critical security feature of SILO. Secrets (API keys, tokens) are **never** passed via shell environment variables (where they can be leaked in logs or to other processes).

### How it works:
1. The **Runner** decrypts secrets from the encrypted vault using the `SILO_MASTER_KEY`.
2. It opens a pipe to the child process's **STDIN**.
3. It sends a JSON payload containing only the secrets required by that specific skill.
4. The `require_secret()` function reads from STDIN and caches the secret in memory.

For production workloads, SILO also supports priority secret retrieval from [HashiCorp Vault](../integrations/vault.md).

## 3. Local Vault Encryption

SILO stores your credentials in `~/.silo/credentials.silo`.

- **Encryption**: AES-256-GCM (Authenticated Encryption).
- **Master Key**: Requires a `SILO_MASTER_KEY` environment variable on the host or a Keyring login.
- **Keyring**: On macOS, SILO integrates with Keychain for seamless, secure storage of the master key.

## 4. Headless vs. Interactive

- **Headless Mode**: Set `SILO_HEADLESS=1` to fail-fast if a secret is missing or approval is needed.
- **Interactive Mode**: SILO opens a local browser window (`interaction.py`) for the human to securely enter a token or approve a sensitive action.

---

**Next:** Learn how [Dynamic Routing](../guide/routing.md) helps Agents find your tools.
