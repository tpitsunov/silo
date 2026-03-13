# Configuration: `silo.yaml`

The `silo.yaml` file is the central configuration for your local SILO environment. It is typically located in `~/.silo/silo.yaml`.

## Global Settings

| Key | Type | Description |
|-----|------|-------------|
| `master_key_strategy` | `string` | How to handle the master key: `env`, `keyring`, or `prompt`. |
| `max_workers` | `int` | Maximum concurrent tool executions (default: `10`). |
| `hub_path` | `string` | custom path for the skill hub. |

## Pruning Logic

Configure how SILO cleans up old skill data and virtual environments.

```yaml
pruning:
  enabled: true
  keep_days: 14            # Removes skills not used in X days
  delete_unused_venv: true # Deletes .venv while keeping the skill source
```

## Secret Mappings

Map local skill secret requirements to global encrypted values.

```yaml
mappings:
  - namespace: "fin-ops"
    secrets:
      API_KEY: "CLAUDE_PRODUCTION_KEY"
```

In this example, the `fin-ops` skill will receive the value stored in the global vault under `CLAUDE_PRODUCTION_KEY` when it requests `require("API_KEY")`.

---

**Next:** Learn how to [Integrate with Claude Desktop](../integrations/claude.md).
