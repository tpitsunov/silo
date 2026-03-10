# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "silo",
# ]
# ///

from silo import Skill, Secret

app = Skill(name="Todoist Skill", description="Add and read tasks from Todoist")

@app.command()
def add_task(content: str):
    """Adds a new task to your Todoist inbox."""
    token = Secret.require("TODOIST_API_TOKEN")
    return f"Task '{content}' added successfully! (mocked, used token ending in ...{token[-4:] if token else ''})"

if __name__ == "__main__":
    app.run()
