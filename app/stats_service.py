
from datetime import datetime, timedelta
import httpx
from .database import stats_collection, history_collection
from .github_api import fetch_from_github

async def compute_language_stats(username: str):
    existing = await stats_collection.find_one({"username": username})

    if existing:
        age = datetime.utcnow() - existing["fetched_at"]
        if age < timedelta(hours=24):
            return existing, True  # cached

    # Fetch repos
    repo_url = f"https://api.github.com/users/{username}/repos"
    repos = await fetch_from_github(repo_url)
    
    total_langs = {}

    async with httpx.AsyncClient() as client:
        for repo in repos:
            lang_url = repo["languages_url"]
            response = await client.get(lang_url)
            lang_data = response.json()

            for lang, bytes_count in lang_data.items():
                total_langs[lang] = total_langs.get(lang, 0) + bytes_count

    total_bytes_value = sum(total_langs.values())
    percentages = {
        lang: float(f"{(count / total_bytes_value) * 100:.2f}")
        for lang, count in total_langs.items()
    }

    data = {
        "username": username,
        "total_bytes": total_langs,
        "percentages": percentages,
        "fetched_at": datetime.utcnow()
    }

    # update latest snapshot
    await stats_collection.update_one(
        {"username": username}, {"$set": data}, upsert=True
    )

    # add to history
    await history_collection.insert_one(data)

    return data, False
