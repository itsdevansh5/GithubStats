
from datetime import datetime, timedelta
import httpx
from .database import stats_collection, history_collection
from .github_api import fetch_from_github


async def compute_language_stats(username: str):
    existing = await stats_collection.find_one({"username": username})

    # 24-hour cache system
    if existing:
        age = datetime.utcnow() - existing["fetched_at"]
        if age < timedelta(hours=24):
            return existing, True

    # Fetch repos
    repo_url = f"https://api.github.com/users/{username}/repos"
    repos = await fetch_from_github(repo_url)

    total_langs = {}

    async with httpx.AsyncClient() as client:
        for repo in repos:

            # 1️⃣ Skip forked repos
            if repo.get("fork"):
                continue

            # 2️⃣ Skip archived repos
            if repo.get("archived"):
                continue

            # Fetch language data
            lang_url = repo["languages_url"]
            response = await client.get(lang_url)
            lang_data = response.json()

            # 3️⃣ Skip repos with no language data
            if not lang_data:
                continue

            # 4️⃣ Skip huge repos (dominant repo filter)
            if sum(lang_data.values()) > 5_000_000:  # 5MB threshold
                continue

            # Aggregate totals
            for lang, bytes_count in lang_data.items():
                total_langs[lang] = total_langs.get(lang, 0) + bytes_count

    if not total_langs:
        raise HTTPException(404, "No valid repositories found for this user")

    total_bytes = sum(total_langs.values())

    # Calculate percentages
    percentages = {
        lang: float(f"{(count / total_bytes) * 100:.2f}")
        for lang, count in total_langs.items()
    }

    # 5️⃣ Remove languages <1% (except if they are the only languages)
    if len(percentages) > 1:
        percentages = {k: v for k, v in percentages.items() if v >= 1.0}
        total_langs = {k: total_langs[k] for k in percentages.keys()}

    data = {
        "username": username,
        "total_bytes": total_langs,
        "percentages": percentages,
        "fetched_at": datetime.utcnow()
    }

    # Save cache & history
    await stats_collection.update_one(
        {"username": username}, {"$set": data}, upsert=True
    )
    await history_collection.insert_one(data)

    return data, False
