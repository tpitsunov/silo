# Deep Dive: Interactive Approvals

SILO bridges the gap between automated agents and human control through its **Interactive Layer**. This ensures that critical actions (like deleting data or spending money) always have a "Human in the Loop."

## 1. Defining Approval Requirements

In your `Skill` definition, you can mark specific tools as requiring approval:

```python
@skill.tool(require_approval=True, time_to_live=300)
def delete_user(user_id: str):
    # ...
```

- **`require_approval`**: Forces SILO to pause execution until a human confirms.
- **`time_to_live`**: The "grace period" (in seconds). If the same agent calls the same tool with the same arguments within this window, it won't ask again.

## 2. The Browser Prompt

If SILO is running on a machine with a display (and not in headless mode), it will start a temporary micro-server and open your default browser.

- **URL**: `http://localhost:<random_port>/`
- **Content**: A premium, branded page showing the tool name, the exact arguments the Agent is trying to pass, and a "Approve" / "Reject" button.
- **Security**: The prompt is tied to a specific execution session.

## 3. The TTY Fallback

Running on a remote server via SSH? SILO detects the absence of a display and falls back to a **Rich Terminal Prompt**:

```text
⚠️  Approval Required
Action: delete_user
Args: {"user_id": "12345"}
Proceed? [y/N]:
```

## 4. Why it Matters

Interactive approvals prevent:
- **Prompt Injection**: An Agent tricked into calling a destructive command.
- **Recursive Loops**: An Agent accidentally calling a costly API thousands of times.
- **Drift**: An Agent making decisions that deviate from the user's intent.

---

**Next:** Check out the [CLI Reference](../reference/cli.md).
