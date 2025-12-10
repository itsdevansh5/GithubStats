
from datetime import datetime, timedelta
import httpx
from fastapi import HTTPException
from .database import stats_collection, history_collection
from .github_api import fetch_from_github


async def compute_language_stats(username: str):

    # ----------------------------
    # 1️⃣ CACHE CHECK (24 HOURS)
    # ----------------------------
    existing = await stats_collection.find_one({"username": username})
    if existing:
        age = datetime.utcnow() - existing["fetched_at"]
        if age < timedelta(hours=24):
            return existing, True  # return cached version

    # ----------------------------
    # 2️⃣ FETCH USER REPOS
    # ----------------------------
    repo_url = f"https://api.github.com/users/{username}/repos"
    repos = await fetch_from_github(repo_url)

    total_langs = {}

    # ----------------------------
    # 3️⃣ PROCESS EACH REPO
    # ----------------------------
    async with httpx.AsyncClient() as client:
        for repo in repos:

            # Skip forked repos
            if repo.get("fork"):
                continue

            # Skip archived repos
            if repo.get("archived"):
                continue

            # Fetch languages for this repo
            lang_url = repo["languages_url"]
            response = await client.get(lang_url)

            # GitHub sometimes returns invalid JSON (rate limit / HTML / [])
            try:
                lang_data = response.json()
            except Exception:
                continue  # skip repo if invalid JSON

            # Skip if not a proper dict
            if not isinstance(lang_data, dict) or not lang_data:
                continue

            # Skip if values are not integers (GitHub weird responses)
            if not all(isinstance(v, int) for v in lang_data.values()):
                continue

            # Skip extremely large repos that dominate stats (e.g., ML repos)
            repo_size = sum(lang_data.values())
            if repo_size > 5_000_000:   # 5 MB threshold
                continue

            # Aggregate totals
            for lang, bytes_count in lang_data.items():
                total_langs[lang] = total_langs.get(lang, 0) + bytes_count

    # ----------------------------
    # 4️⃣ VALIDATION CHECK
    # ----------------------------
    if not total_langs:
        raise HTTPException(404, "No valid repositories found for this user")

    total_bytes = sum(total_langs.values())

    # ----------------------------
    # 5️⃣ CALCULATE PERCENTAGES
    # ----------------------------
    percentages = {
        lang: float(f"{(count / total_bytes) * 100:.2f}")
        for lang, count in total_langs.items()
    }

    # ----------------------------
    # 6️⃣ REMOVE LANGUAGES <1%
    # ----------------------------
    if len(percentages) > 1:
        percentages = {k: v for k, v in percentages.items() if v >= 1.0}
        total_langs = {k: total_langs[k] for k in percentages.keys()}

    # ----------------------------
    # 7️⃣ FINAL DATA OBJECT
    # ----------------------------
    data = {
        "username": username,
        "total_bytes": total_langs,
        "percentages": percentages,
        "fetched_at": datetime.utcnow()
    }

    # ----------------------------
    # 8️⃣ SAVE SNAPSHOT & CACHE
    # ----------------------------
    await stats_collection.update_one(
        {"username": username}, {"$set": data}, upsert=True
    )

    await history_collection.insert_one(data)

    return data, False
