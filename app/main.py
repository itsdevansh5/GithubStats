from .svg_generator import generate_stats_svg
from fastapi import FastAPI, HTTPException, Request
from .stats_service import compute_language_stats
from .database import create_mongo_client
from .models import StatsResponse,GithubUsername
from fastapi.responses import Response
from .exceptions import GithubRateLimitError,GithubServerError
from contextlib import asynccontextmanager
from .redis_caching import create_redis_client
from dotenv import load_dotenv
import httpx
import os

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.github_client = httpx.AsyncClient(
            headers = HEADERS,
            timeout = httpx.Timeout(5.0)
            )

    app.state.redis_client = create_redis_client()
    app.state.mongo_client,app.state.db = create_mongo_client()
    

    yield

    await app.state.github_client.aclose()
    await app.state.redis_client.aclose()
    await app.state.mongo_client.aclose()

app = FastAPI(lifespan = lifespan)

@app.get("/")
def home():
    return {"message": "GitHub Stats API Running"}

@app.get("/stats/{username}", response_model=StatsResponse)
async def get_stats(username: GithubUsername, request: Request):

    client = request.app.state.github_client
    redis_client = request.app.state.redis_client
    mongo_client = request.app.state.mongo_client
    db = request.app.state.db  
  
    try:
        data, cached = await compute_language_stats(username,client,
                                                          redis_client,db)
    except GithubRateLimitError:
        raise HTTPException(
            status_code=503,
            detail="GitHub Rate Limit Exhausted"
          )
    except GithubServerError:
        raise HTTPException(
            status_code=503,
            detail="Github is currently unavailable"
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
