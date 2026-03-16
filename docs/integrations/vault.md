# HashiCorp Vault Integration

SILO supports HashiCorp Vault as a priority source for secrets. When Vault is configured, SILO will attempt to fetch secrets from it before falling back to the local Keychain or credentials file.

## Configuration

To activate Vault integration, set the following environment variables:

- `VAULT_ADDR`: Your Vault server URL (e.g., `https://vault.example.com:8200`).
- `VAULT_TOKEN`: Your Vault access token.
- `VAULT_NAMESPACE` (optional): The Vault namespace (if using Vault Enterprise).

## Secret Structure

By default, SILO looks for secrets in the KV engine (both V1 and V2 are supported) under the path `silo`.

Example structure in Vault (KV V2):

```json
{
  "data": {
    "OPENAI_API_KEY": "sk-...",
    "DATABASE_URL": "postgres://..."
  }
}
```

In your skill code, fetching a secret remains identical:

```python
from silo import secrets

api_key = secrets.require("OPENAI_API_KEY")
```

SILO will automatically check Vault first. If the secret is found there, it will be used immediately.

## Benefits

1. **Centralization**: All secrets are stored in one secure, audited location.
2. **Dynamic Management**: Changes in Vault take effect immediately for new skill executions.
3. **Security**: Secrets are not stored locally on disk if they are retrieved from Vault.
