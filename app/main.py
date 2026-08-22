from .svg_generator import generate_stats_svg
from fastapi import FastAPI, HTTPException
from .stats_service import compute_language_stats
from .database import history_collection
from .models import StatsResponse,GithubUsername
from fastapi.responses import Response
from .exceptions import GithubRateLimitError

app = FastAPI()

@app.get("/")
def home():
    return {"message": "GitHub Stats API Running"}

@app.get("/stats/{username}", response_model=StatsResponse)
async def get_stats(username: GithubUsername):
    try:
        data, cached = await compute_language_stats(username)
    except GithubRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="GitHub Rate Limit Exhausted"
          )        
        
    data["cached"] = cached
    return data

@app.get("/history/{username}")
async def get_history(username: GithubUsername):
    cursor = history_collection.find({"username": username}).sort("fetched_at", 1)
    history = []

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        history.append(doc)

    if not history:
        raise HTTPException(status_code=404, detail="No history found.")

    return {
        "username": username,
        "history": history
    }


@app.get("/card/stats/{username}")
async def stats_card(username: GithubUsername):
    data, _ = await compute_language_stats(username)
    
    svg = generate_stats_svg(
        username=data["username"],
        percentages=data["percentages"]
    )
    
    return Response(content=svg, media_type="image/svg+xml",headers={
            # "public" = intermediate proxies (like GitHub Camo) can cache it
            # "max-age=14400" = Keep this in cache for 4 hours
            "Cache-Control": "public, max-age=14400"
        })   
