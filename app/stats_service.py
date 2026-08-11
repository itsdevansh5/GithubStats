from datetime import datetime, timedelta
from fastapi import HTTPException

from .database import stats_collection, history_collection
from .github_service import (
    get_user_repositories,
    fetch_all_repository_languages,
)


async def compute_language_stats(username: str):

    # --------------------------------
    # 1. CHECK CACHE (24 HOURS)
    # --------------------------------
    existing = await stats_collection.find_one({"username": username})

    if existing:
        age = datetime.utcnow() - existing["fetched_at"]

        if age < timedelta(hours=24):
            return existing, True

    # --------------------------------
    # 2. FETCH USER REPOSITORIES
    # --------------------------------
    repos = await get_user_repositories(username)

    # --------------------------------
    # 3. FETCH LANGUAGE DATA
    # --------------------------------
    language_data = await fetch_all_repository_languages(repos)

    # --------------------------------
    # 4. AGGREGATE LANGUAGE TOTALS
    # --------------------------------
    total_langs = {}

    for repo_languages in language_data:

        

        for language, bytes_count in repo_languages.items():
            total_langs[language] = (
                total_langs.get(language, 0) + bytes_count
            )

    # --------------------------------
    # 5. VALIDATION
    # --------------------------------
    if not total_langs:
        raise HTTPException(
            status_code=404,
            detail="No valid repositories found for this user",
        )

    # --------------------------------
    # 6. CALCULATE PERCENTAGES
    # --------------------------------
    total_bytes = sum(total_langs.values())

    percentages = {
        language: float(f"{(count / total_bytes) * 100:.2f}")
        for language, count in total_langs.items()
    }

    # --------------------------------
    # 7. REMOVE LANGUAGES BELOW 1%
    # --------------------------------
    if len(percentages) > 1:

        percentages = {
            language: percentage
            for language, percentage in percentages.items()
            if percentage >= 1.0
        }

        total_langs = {
            language: total_langs[language]
            for language in percentages
        }

    # --------------------------------
    # 8. BUILD FINAL DATA
    # --------------------------------
    data = {
        "username": username,
        "total_bytes": total_langs,
        "percentages": percentages,
        "fetched_at": datetime.utcnow(),
    }

    # --------------------------------
    # 9. SAVE CACHE
    # --------------------------------
    await stats_collection.update_one(
        {"username": username},
        {"$set": data},
        upsert=True,
    )

    # --------------------------------
    # 10. SAVE HISTORY SNAPSHOT
    # --------------------------------
    await history_collection.insert_one(data)

    return data, False
