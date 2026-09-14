import json
from unittest.mock import AsyncMock,MagicMock
import pytest
from app.stats_service import compute_language_stats
@pytest.mark.asyncio
async def test_compute_language_stats_cache_hit(monkeypatch):

    cached_data = {
        "username": "devansh",
        "language_aggregate": {
            "Python": 1000
        },
        "percentages": {
            "Python": 100.0
        },
        "total_repos": 5,
        "fetched_at": "2026-09-14T00:00:00+00:00",
        "total_bytes": 1000
    }

    github_repos = AsyncMock()
    github_languages = AsyncMock()

    monkeypatch.setattr(
    "app.stats_service.get_user_repositories",
    github_repos
    )

    monkeypatch.setattr(
    "app.stats_service.fetch_all_repository_languages",
    github_languages
    )

    redis_client = AsyncMock()
    redis_client.get.return_value = json.dumps(cached_data)

    client = AsyncMock()
    db = AsyncMock()

    result, from_cache = await compute_language_stats(
        "devansh",
        client,
        redis_client,
        db
    )

    assert result == cached_data
    assert from_cache is True

    redis_client.get.assert_awaited_once_with(
        "gh:langpct:devansh"
    )


    github_repos.assert_not_awaited()
    github_languages.assert_not_awaited()


@pytest.mark.asyncio
async def test_redis_cache_miss(monkeypatch):
    
    redis_client = AsyncMock()
    redis_client.get.return_value = None
    client = AsyncMock()
    db = MagicMock()
    history_collection  = AsyncMock()
    db.__getitem__.return_value = history_collection

    async def fake_get_user_repositories(username, client):
        return [
        {
            "name": "repo1",
            "languages_url": "https://api.github.com/repos/devansh/repo1/languages",
        },
        {
            "name": "repo2",
            "languages_url": "https://api.github.com/repos/devansh/repo2/languages",
        },
        ]

    async def fake_fetch_all_repository_languages(repos, client):
        return [
        {
            "Python": 600,
            "JavaScript": 400,
        },
        {
            "Python": 400,
        },
        ]

    monkeypatch.setattr(
    "app.stats_service.get_user_repositories",
    fake_get_user_repositories,
    )

    monkeypatch.setattr(
    "app.stats_service.fetch_all_repository_languages",
    fake_fetch_all_repository_languages,
    )

    
    
    result, cached = await compute_language_stats(
    "devansh",
    client,
    redis_client,
    db
    )

    assert cached is False

    assert result["language_aggregate"] == {
    "Python": 1000,
    "JavaScript": 400,
    }

    assert result["percentages"] == {
    "Python": 71.43,
    "JavaScript": 28.57,
    }

    assert result["total_repos"] == 2
    assert result["total_bytes"] == 1400

    redis_client.set.assert_awaited_once()
    history_collection.insert_one.assert_awaited_once()

    
