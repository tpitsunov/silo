# Skill SDK Reference

The `silo.skill` SDK is used to build native SILO tools.

## The `Skill` Class

```python
from silo.skill import Skill
skill = Skill(namespace="my_namespace")
```

## Decorators

### `@skill.tool(require_approval=False, time_to_live=600)`
Registers a function as an agent-callable tool.

- **`require_approval`**: If True, SILO will pause execution and request user approval.
- **`time_to_live`**: Duration in seconds a single approval is valid for.

### `@skill.instructions()`
Allows defining a high-level manual or "spirit" for the skill. This is injected into the Agent's context.

## Secrets Management

### `silo.secrets.require(key_name: str) -> str`
Requests a secret by name. SILO handles the decryption and secure injection.
If the secret is missing, it will automatically trigger a browser-based prompt unless running in headless mode.

## Response Types

### `AgentResponse`
The recommended return type for complex tools.
```python
from silo.types import AgentResponse
return AgentResponse(llm_text="Short summary", raw_data={"detail": "..."})
```
