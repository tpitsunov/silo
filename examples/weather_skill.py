# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "silo",
#     "httpx",
# ]
# ///

from silo import Skill, JSONResponse

app = Skill(name="Weather Skill", description="Get current weather for a city.")

@app.command()
def get_weather(city: str):
    """Fetches the current weather for the specified city."""
    import httpx
    # Normally we would use Secret.require("WEATHER_API_KEY") 
    # and hit a real API, but this is just a quick example of uv isolation!
    
    # Using a free mock API or similar
    url = f"https://wttr.in/{city}?format=j1"
    try:
        r = httpx.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        current = data.get("current_condition", [{}])[0]
        temp = current.get("temp_C", "Unknown")
        desc = current.get("weatherDesc", [{"value": "Unknown"}])[0]["value"]
        
        return JSONResponse({"city": city, "temperature_c": temp, "condition": desc})
    except Exception as e:
        return JSONResponse({"error": str(e), "city": city})

if __name__ == "__main__":
    app.run()
