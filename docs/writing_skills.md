# Writing Skills

This guide explores the core concepts of creating commands in SILO.

## The `Skill` Class

A SILO skill is an instance of the `Skill` class, which manages all commands, argument parsing, error handling, and serialization.

```python
from silo import Skill

app = Skill(name="My Skill", description="A description of what it does.")
```

## Creating Commands

Commands are functions decorated with `@app.command()`. SILO reads the function signature to determine the command's arguments, types, and defaults.

```python
@app.command()
def greet(name: str, shout: bool = False):
    """Greets a user by name."""
    msg = f"Hello, {name}!"
    if shout:
        msg = msg.upper()
    return {"message": msg}
```

SILO automatically maps the above signature to standard CLI flags:
```bash
uv run my_skill.py greet --name Alice --shout True
```

## Using Pydantic for Complex Input

LLMs are excellent at writing JSON. If your command requires a complex structure (like an object or a list of items), use **Pydantic Model**s as argument types instead of passing long lists of separate arguments.

SILO will automatically accept a JSON string from the command line, validate it against your model, and pass the parsed object to your function.

```python
from pydantic import BaseModel
from silo import Skill, JSONResponse

app = Skill("issue_tracker")

class Issue(BaseModel):
    title: str
    body: str

@app.command()
def create_issue(repo: str, detail: Issue):
    """Creates a new issue in a repository."""
    # detail is now a fully typed Pydantic object
    print(f"Creating issue '{detail.title}' in {repo}")
    
    return JSONResponse(
        {"status": "created", "repo": repo, "issue": detail.title}
    )
```

Usage from the CLI:
```bash
uv run my_skill.py create_issue \
    --repo "user/repo" \
    --detail '{"title": "Bug", "body": "Fixed"}'
```

If the JSON string passed to `--detail` does not match the Pydantic model structure, SILO will gracefully return a clear JSON error telling the LLM exactly which required fields were missing or incorrectly typed.

## Structuring the Output

When returning data from a SILO command, ALWAYS return a clean, structured object (dictionary, list, or a `SiloResponse`). Agents communicate via text streams, so they don't look at typical `print()` outputs the way a human does. They look for parsable output, like JSON or Markdown.

SILO provides helper response classes:

- **`JSONResponse(dict_or_list)`**: Converts the output into prettified `json.dumps()` output.
- **`MarkdownResponse(str)`**: Wrapper indicating that the return value is formatted text.

```python
from silo import Skill, JSONResponse, MarkdownResponse

app = Skill("format_tool")

@app.command()
def get_stats():
    # Recommended: returning JSON for the agent to parse programmatically
    return JSONResponse({"active": True, "users": 42})

@app.command()
def get_readme():
    # Recommended: returning clear Markdown content
    return MarkdownResponse("# Project README\n\nThis is the content.")
```
