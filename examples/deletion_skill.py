from silo import Skill, JSONResponse
import sys

app = Skill(name="Danger Zone", description="A skill with critical actions.")

@app.command(require_approval=True)
def delete_everything(confirm: bool = False):
    """
    DELETES EVERYTHING. Use with extreme caution.
    """
    if confirm:
        return JSONResponse({"status": "SUCCESS", "message": "The world has been deleted."})
    return JSONResponse({"status": "ABORTED", "message": "Safe!"})

if __name__ == "__main__":
    app.run()
