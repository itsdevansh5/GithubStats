from fastapi.testclient import TestClient
from unittest.mock import AsyncMock,MagicMock
from app.main import app
from app.exceptions import GithubRateLimitError,GithubServerError


class FakeCursor:

    def __init__(self, history):
        self.history = history

    def sort(self, field, direction):
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.history:
            raise StopAsyncIteration

        return self.history.pop(0)


def test_get_stats_success(monkeypatch):

    fake_data = {
        "username": "devansh",
        "language_aggregate": {
            "Python": 1000,
            "JavaScript": 500,
        },
        "percentages": {
            "Python": 66.67,
            "JavaScript": 33.33,
        },
        "total_repos": 2,
        "fetched_at": "2026-09-16T00:00:00+00:00",
        "total_bytes": 1500,
    }

    fake_compute = AsyncMock(
        return_value=(fake_data, False)
    )

    monkeypatch.setattr(
        "app.main.compute_language_stats",
        fake_compute,
    )

    with TestClient(app) as client:
        response = client.get("/stats/devansh")

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "devansh"
    assert data["language_aggregate"] == {
        "Python": 1000,
        "JavaScript": 500,
    }
    assert data["cached"] is False



def test_get_stats_rate_limit(monkeypatch):

    fake_compute = AsyncMock(
        side_effect=GithubRateLimitError()
    )

    monkeypatch.setattr(
        "app.main.compute_language_stats",
        fake_compute,
    )

    with TestClient(app) as client:
        response = client.get("/stats/devansh")

    assert response.status_code == 503
    assert response.json()["detail"] == "GitHub Rate Limit Exhausted"


def test_get_stats_github_server_error(monkeypatch):

    fake_compute = AsyncMock(
        side_effect=GithubServerError()
    )

    monkeypatch.setattr(
        "app.main.compute_language_stats",
        fake_compute,
    )

    with TestClient(app) as client:
        response = client.get("/stats/devansh")

    assert response.status_code == 503
    assert response.json()["detail"] == "Github is currently unavailable"


def test_get_history_success(monkeypatch):

    fake_history = [
        {
            "_id": "abc123",
            "username": "devansh",
            "percentages": {
                "Python": 80.0
            },
            "fetched_at": "2026-09-15T10:00:00+00:00",
        },
        {
            "_id": "def456",
            "username": "devansh",
            "percentages": {
                "Python": 70.0
            },
            "fetched_at": "2026-09-16T10:00:00+00:00",
        },
    ]

    history_collection = MagicMock()

    history_collection.find.return_value = FakeCursor(
        fake_history.copy()
    )

    db = MagicMock()
    db.__getitem__.return_value = history_collection
    
    mongo_client = MagicMock()

    monkeypatch.setattr(
        "app.main.create_mongo_client",
        lambda: (mongo_client, db)
    )

    
    with TestClient(app) as client:
        response = client.get("/history/devansh")

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "devansh"

    assert data["history"] == [
        {
            "_id": "abc123",
            "username": "devansh",
            "percentages": {
                "Python": 80.0
            },
            "fetched_at": "2026-09-15T10:00:00+00:00",
        },
        {
            "_id": "def456",
            "username": "devansh",
            "percentages": {
                "Python": 70.0
            },
            "fetched_at": "2026-09-16T10:00:00+00:00",
        },
    ]

    history_collection.find.assert_called_once_with(
        {"username": "devansh"}
    )
 
def test_get_history_not_found(monkeypatch):
    history_collection = MagicMock()
    history_collection.find.return_value = FakeCursor([])

    db = MagicMock()
    db.__getitem__.return_value = history_collection

    mongo_client = MagicMock()

    monkeypatch.setattr(
        "app.main.create_mongo_client",
        lambda: (mongo_client, db)
    )

    with TestClient(app) as client:
        response = client.get("/history/devansh")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No history found."
    }

    history_collection.find.assert_called_once_with(
        {"username": "devansh"}
    )


def test_get_history_converts_id_to_string(monkeypatch):
    fake_history = [
        {
            "_id": 12345,
            "username": "devansh",
            "percentages": {"Python": 80.0},
            "fetched_at": "2026-09-15T10:00:00+00:00",
        }
    ]

    history_collection = MagicMock()
    history_collection.find.return_value = FakeCursor(fake_history.copy())

    db = MagicMock()
    db.__getitem__.return_value = history_collection

    mongo_client = MagicMock()

    monkeypatch.setattr(
        "app.main.create_mongo_client",
        lambda: (mongo_client, db)
    )

    with TestClient(app) as client:
        response = client.get("/history/devansh")

    assert response.status_code == 200

    data = response.json()

    assert data["history"][0]["_id"] == "12345"


def test_get_history_orders_by_fetched_at(monkeypatch):
    fake_history = [
        {
            "_id": "new",
            "username": "devansh",
            "fetched_at": "2026-09-16T10:00:00+00:00",
        },
        {
            "_id": "old",
            "username": "devansh",
            "fetched_at": "2026-09-15T10:00:00+00:00",
        },
    ]

    cursor = MagicMock()
    cursor.sort.return_value = FakeCursor(fake_history.copy())

    history_collection = MagicMock()
    history_collection.find.return_value = cursor

    db = MagicMock()
    db.__getitem__.return_value = history_collection

    mongo_client = MagicMock()

    monkeypatch.setattr(
        "app.main.create_mongo_client",
        lambda: (mongo_client, db)
    )

    with TestClient(app) as client:
        response = client.get("/history/devansh")

    assert response.status_code == 200

    cursor.sort.assert_called_once_with("fetched_at", 1)


def test_stats_card_success(monkeypatch):
    fake_data = {
        "username": "devansh",
        "percentages": {
            "Python": 70.0,
            "C++": 30.0,
        },
        "total_bytes": 1000,
        "total_repos": 5,
        "fetched_at": "2026-09-16T10:00:00+00:00",
    }

    async def fake_compute_language_stats(*args):
        return fake_data, False

    monkeypatch.setattr(
        "app.main.compute_language_stats",
        fake_compute_language_stats
    )

    with TestClient(app) as client:
        response = client.get("/card/stats/devansh")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")

    assert "devansh" in response.text
    assert "Python" in response.text
    assert "C++" in response.text

def test_stats_card_returns_valid_svg(monkeypatch):
    fake_data = {
        "username": "devansh",
        "percentages": {
            "Python": 80.0,
        },
        "total_bytes": 1000,
        "total_repos": 3,
        "fetched_at": "2026-09-16T10:00:00+00:00",
    }

    async def fake_compute_language_stats(*args):
        return fake_data, False

    monkeypatch.setattr(
        "app.main.compute_language_stats",
        fake_compute_language_stats
    )

    with TestClient(app) as client:
        response = client.get("/card/stats/devansh")

    assert response.status_code == 200
    assert response.text.startswith("<svg")
    assert "</svg>" in response.text

def test_stats_card_calls_compute_service(monkeypatch):
    fake_data = {
        "username": "devansh",
        "percentages": {"Python": 100.0},
        "total_bytes": 500,
        "total_repos": 2,
        "fetched_at": "2026-09-16T10:00:00+00:00",
    }

    called = False

    async def fake_compute_language_stats(*args):
        nonlocal called
        called = True
        return fake_data, False

    monkeypatch.setattr(
        "app.main.compute_language_stats",
        fake_compute_language_stats
    )

    with TestClient(app) as client:
        response = client.get("/card/stats/devansh")

    assert response.status_code == 200
    assert called is True 




def test_stats_card_returns_valid_svg(monkeypatch):
    fake_data = {
        "username": "devansh",
        "percentages": {
            "Python": 80.0,
        },
        "total_bytes": 1000,
        "total_repos": 3,
        "fetched_at": "2026-09-16T10:00:00+00:00",
    }

    async def fake_compute_language_stats(*args):
        return fake_data, False

    monkeypatch.setattr(
        "app.main.compute_language_stats",
        fake_compute_language_stats
    )

    with TestClient(app) as client:
        response = client.get("/card/stats/devansh")

    assert response.headers["cache-control"]=="public, max-age=14400"
