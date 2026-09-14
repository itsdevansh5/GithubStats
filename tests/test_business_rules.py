import pytest
from app.stats_service import compute_language_stats
from unittest.mock import AsyncMock,MagicMock
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_compute_language_stats_no_valid_repositories(monkeypatch):

    redis_client = AsyncMock()
    redis_client.get.return_value = None

    client = AsyncMock()

    async def fake_get_user_repositories(username, client):
        return [
            {"name": "repo1"},
            {"name": "repo2"},
        ]

    async def fake_fetch_all_repository_languages(repos, client):
        return []

    monkeypatch.setattr(
        "app.stats_service.get_user_repositories",
        fake_get_user_repositories,
    )

    monkeypatch.setattr(
        "app.stats_service.fetch_all_repository_languages",
        fake_fetch_all_repository_languages,
    )

    with pytest.raises(HTTPException) as exc_info:
        await compute_language_stats(
            "devansh",
            client,
            redis_client,
            MagicMock(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No valid repositories found for this user"


@pytest.mark.asyncio
async def test_compute_language_stats_filters_languages_below_one_percent(
    monkeypatch,
):
    redis_client = AsyncMock()
    redis_client.get.return_value = None

    client = AsyncMock()

    db = MagicMock()
    history_collection = AsyncMock()
    db.__getitem__.return_value = history_collection

    async def fake_get_user_repositories(username, client):
        return [
            {"name": "repo1"},
        ]

    async def fake_fetch_all_repository_languages(repos, client):
        return [
            {
                "Python": 1000,
                "JavaScript": 100,
                "Go": 5,
            }
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
        db,
    )

    assert cached is False

    assert "Go" not in result["percentages"]
    assert "Go" not in result["language_aggregate"]

    assert result["percentages"]["Python"] == 90.5
    assert result["percentages"]["JavaScript"] == 9.05

    assert result["language_aggregate"] == {
        "Python": 1000,
        "JavaScript": 100,
    }
