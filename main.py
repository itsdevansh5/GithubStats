from database import stats_collection,history_collection
from datetime import datetime,timedelta
from fastapi import *
import httpx

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to Github Stats API"}

@app.get("/hello/{name}")
def greet(name: str):
    return {"message": f"Hello {name}, welcome to the API!"}

async def fetch_from_github(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="GitHub API error or user not found"
        )

    return response.json()

async def get_repo_languages(languages_url: str):
    return await fetch_from_github(languages_url)

@app.get("/repos/{username}")
async def get_repos(username: str):
    url = f"https://api.github.com/users/{username}/repos"
    repos = await fetch_from_github(url)

    clean_data = [
        {
            "name": repo["name"],
            "url": repo["html_url"],
            "languages_url": repo["languages_url"]
        }
        for repo in repos
    ]

    return clean_data


@app.get("/stats/{username}")
async def get_language_stats(username: str):
    # 1️⃣ Check cache (if data exists in last 24 hours)
    existing = await stats_collection.find_one({"username": username})

    if existing:
        # check if older than 24 hours
        age = datetime.utcnow() - existing["fetched_at"]
        if age < timedelta(hours=24):
            return {
                "username": existing["username"],
                "cached": True,
                "percentages": existing["percentages"],
                "total_bytes": existing["total_bytes"]
            }

    # 2️⃣ Fetch fresh data from GitHub
    url = f"https://api.github.com/users/{username}/repos"
    repos = await fetch_from_github(url)

    total_langs = {}

    async with httpx.AsyncClient() as client:
        for repo in repos:
            lang_url = repo["languages_url"]
            response = await client.get(lang_url)
            lang_data = response.json()

            for lang, bytes_count in lang_data.items():
                total_langs[lang] = total_langs.get(lang, 0) + bytes_count

    total_bytes = sum(total_langs.values())
    percentages = {
        lang: float(f"{(count / total_bytes) * 100:.2f}")
        for lang, count in total_langs.items()
    }

    # 3️⃣ Save to database
    data = {
        "username": username,
        "total_bytes": total_langs,
        "percentages": percentages,
        "fetched_at": datetime.utcnow()
    }

# 4️⃣ Save the result to history (append)
    await history_collection.insert_one(data)

    await stats_collection.update_one(
        {"username": username},
        {"$set": data},
        upsert=True
    )

    # 4️⃣ Return result
    return {
        "username": username,
        "cached": False,
        "total_bytes": total_langs,
        "percentages": percentages
    }
    
@app.get("/history/{username}")
async def get_history(username: str):
    cursor = history_collection.find({"username": username}).sort("fetched_at", 1)
    
    history = []
    async for doc in cursor:
        history.append({
            "fetched_at": doc["fetched_at"],
            "percentages": doc["percentages"],
            "total_bytes": doc["total_bytes"]
        })

    if not history:
        raise HTTPException(status_code=404, detail="No history found for this user")

    return {
        "username": username,
        "history": history
    }
