
from fastapi import FastAPI, HTTPException
from .stats_service import compute_language_stats
from .database import history_collection
from .models import StatsResponse

app = FastAPI()

@app.get("/")
def home():
    return {"message": "GitHub Stats API Running"}

@app.get("/stats/{username}", response_model=StatsResponse)
async def get_stats(username: str):
    data, cached = await compute_language_stats(username)
    data["cached"] = cached
    return data

@app.get("/history/{username}")
async def get_history(username: str):
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
