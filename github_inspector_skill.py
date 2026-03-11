# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "silo",
#     "requests"
# ]
# ///

from silo import Skill, Secret, JSONResponse
import requests

app = Skill(name="GitHub Inspector", description="Safely inspects a GitHub token to fetch the authenticated user's profile.")

@app.command(require_approval=True)
def inspect_token():
    """
    Safely inspects the provided GitHub token by fetching the authenticated user's profile.
    This action requires approval and only performs a safe GET request.
    """
    token = Secret.require("GITHUB_TOKEN")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        response = requests.get("https://api.github.com/user", headers=headers)
        if response.status_code == 200:
            data = response.json()
            return JSONResponse({
                "status": "SUCCESS",
                "message": "GitHub API key is valid and working!",
                "user": data.get("login"),
                "name": data.get("name"),
                "public_repos": data.get("public_repos")
            })
        else:
            return JSONResponse({
                "status": "ERROR",
                "message": f"Failed to validate token. Status code: {response.status_code}",
                "details": response.text
            })
    except Exception as e:
         return JSONResponse({
            "status": "ERROR",
            "message": str(e)
         })

if __name__ == "__main__":
    app.run()
