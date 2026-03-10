# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "silo",
#     "silo[mcp]", # Required for MCP server functionality
#     "pydantic",
# ]
# ///

from typing import List, Optional
from pydantic import BaseModel, Field
from silo import Skill, Secret

app = Skill(name="GitHub MCP Skill", description="Create and manage GitHub issues via MCP")

class IssueDetails(BaseModel):
    title: str = Field(..., description="The title of the issue.")
    body: str = Field(..., description="The full markdown body description of the issue.")
    labels: Optional[List[str]] = Field(default=None, description="A list of label names to apply.")

@app.command()
def create_issue(repo: str, details: IssueDetails):
    """Creates a new issue in the specified GitHub repository."""
    # This will use exactly the same auth workflow (env -> keychain -> browser)
    # Even when running as an MCP server for Claude Desktop!
    token = Secret.require("GITHUB_API_TOKEN")
    
    # In a real skill, we would make a POST request to api.github.com here
    return {
        "status": "success",
        "action": "created_issue",
        "repository": repo,
        "token_used": f"...{token[-4:]}" if token else None,
        "issue_data": details.model_dump()
    }

if __name__ == "__main__":
    # Start the MCP server using stdio transport
    app.run_mcp()
