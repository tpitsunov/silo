# Tutorial: Building Multi-Tool Skills

Complex skills often require multiple related tools. This guide shows how to group tools and share state (safely) within a single skill.

## 1. Grouping Tools in a Namespace

A SILO Skill is identified by its `namespace`. Every tool registered under that instance becomes part of the namespace.

```python
from silo.skill import Skill

skill = Skill(namespace="system-ops")

@skill.tool()
def get_uptime():
    """Returns the system uptime."""
    # ...

@skill.tool()
def cleanup_temp_files(force: bool = False):
    """Purges the /tmp/ folder."""
    # ...
```

## 2. Shared Logic

Since a skill runs as a single script execution, you can define shared utility functions or classes within the same file.

```python
def _get_api_client():
    from my_client import Client
    return Client(api_key=require_secret("MY_KEY"))

@skill.tool()
def list_resources():
    client = _get_api_client()
    return client.list()
```

## 3. Best Practices for Multi-Tool Skills

- **Atomicity**: Each tool should do one thing and do it well.
- **Clear Descriptions**: Since Agents use BM25 search, ensure each tool in your skill has a unique and descriptive docstring.
- **Shared Secrets**: Use the same secret keys for related tools to minimize approval fatigue.

---

**Next:** Learn how to [Connect to Custom Orchestrators](../integrations/custom.md).
