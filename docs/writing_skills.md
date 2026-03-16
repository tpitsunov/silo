# Writing Skills

This guide explores the core concepts of creating tools in SILO.

## The `Skill` Class

A SILO skill is an instance of the `Skill` class, which manages all tools, argument parsing, error handling, and serialization.

```python
from silo import Skill

skill = Skill(namespace="github")
```

## Creating Tools

Tools are functions decorated with `@skill.tool()`. SILO uses Pydantic via `validate_call` to determine the arguments, types, and defaults.

```python
@skill.tool()
def greet(name: str, shout: bool = False):
    """Greets a user by name."""
    msg = f"Hello, {name}!"
    if shout:
        msg = msg.upper()
    return f"Result: {msg}"
```

SILO automatically maps the above signature to standard CLI flags:
```bash
silo run github greet --name Alice --shout
```
```text title="Output Simulation"
⠋ Executing github:greet...
╭────────────────────────────── Execution Result ───────────────────────────────╮
│ HELLO, ALICE!                                                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Using Pydantic for Complex Input

LLMs are excellent at writing JSON. If your tool requires a complex structure (like an object or a list of items), use **Pydantic Model**s as argument types.

```python
from pydantic import BaseModel
from silo import Skill, AgentResponse

skill = Skill("issue_tracker")

class Issue(BaseModel):
    title: str
    body: str

@skill.tool()
def create_issue(repo: str, detail: Issue):
    """Creates a new issue in a repository."""
    # detail is now a fully typed Pydantic object
    print(f"Creating issue '{detail.title}' in {repo}")
    
    return AgentResponse(
        llm_text=f"Issue '{detail.title}' created in {repo}",
        raw_data={"status": "created", "repo": repo, "issue": detail.title}
    )
```

Usage from the CLI:
```bash
silo run issue_tracker create_issue \
    --repo "user/repo" \
    --detail '{"title": "Bug", "body": "Fixed"}'
```
```text title="Output Simulation"
⠋ Executing issue_tracker:create_issue...
╭────────────────────────────── Execution Result ───────────────────────────────╮
│ Issue 'Bug' created in user/repo                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Managing Secrets

To use sensitive data like API tokens, use `silo.secrets.require()`. SILO will handle secure storage in the OS Keychain and only prompt the user once.

```python
from silo import Skill, require_secret

skill = Skill("github")

@skill.tool()
def get_user():
    token = require_secret("GITHUB_TOKEN")
    # Use token in your API calls...
    return "User data retrieved."
```

## Structuring the Output

When returning data from a SILO tool, you can return:
1. **A string**: Automatically wrapped in a success response.
2. **A dictionary**: Automatically converted to JSON.
3. **`AgentResponse`**: The recommended way to provide separate content for the LLM and the orchestrator.

```python
from silo import Skill, AgentResponse

skill = Skill("github")

@skill.tool()
def get_stats():
    # Providing rich context for the LLM and raw data for the caller
    return AgentResponse(
        llm_text="The repository has 42 active users and is healthy.",
        raw_data={"active_users": 42, "status": "healthy"}
    )
```
