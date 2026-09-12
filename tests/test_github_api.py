from app.github_service import get_next_url
from app.github_service import get_user_repositories,fetch_repository_languages,fetch_all_repository_languages
from app.exceptions import GithubRateLimitError,GithubServerError
import httpx
import respx
import pytest
import asyncio
def test_get_next_url_returns_next_link():
    link = '<https://api.github.com/users/devansh/repos?page=2>; rel="next", <https://api.github.com/users/devansh/repos?page=5>; rel="last"'

    result = get_next_url(link)

    assert result == "https://api.github.com/users/devansh/repos?page=2"

def test_get_next_url_returns_none_when_no_next_link():
    link = '<https://api.github.com/users/devansh/repos?page=5>; rel="last"'

    result = get_next_url(link)

    assert result is None

def test_get_next_url_returns_none_when_link_is_none():
    result = get_next_url(None)

    assert result is None




@pytest.mark.asyncio
async def test_get_user_repositories_follows_pagination():
    page1 = [
        {"id": 1, "name": "repo-one"},
        {"id": 2, "name": "repo-two"},
    ]

    page2 = [
        {"id": 3, "name": "repo-three"},
    ]

    with respx.mock:
        respx.get(
            "https://api.github.com/users/devansh/repos?per_page=100"
        ).mock(
            return_value=httpx.Response(
                200,
                json=page1,
                headers={
                    "Link": '<https://api.github.com/users/devansh/repos?page=2>; rel="next"'
                },
            )
        )

        respx.get(
            "https://api.github.com/users/devansh/repos?page=2"
        ).mock(
            return_value=httpx.Response(
                200,
                json=page2,
            )
        )

        async with httpx.AsyncClient() as client:
            repos = await get_user_repositories("devansh", client)

            assert repos == page1 + page2


@pytest.mark.asyncio
async def test_get_repository_languages_raises_rate_limit_error():
    repo = {
        "languages_url": "https://api.github.com/repos/devansh/test/languages"
    }

    with respx.mock:
        respx.get(
            "https://api.github.com/repos/devansh/test/languages"
        ).mock(
            return_value=httpx.Response(429)
        )

        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(5)

            with pytest.raises(GithubRateLimitError):
                await fetch_repository_languages(
                    repo,
                    semaphore,
                    client,
                )
            assert len(respx.calls) == 1

@pytest.mark.asyncio
async def test_fetch_repository_languages_retries_on_server_error(monkeypatch):
    repo = {
        "languages_url": "https://api.github.com/repos/devansh/test/languages"
    }

    async def fake_sleep(delay):
        pass

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    with respx.mock:
        route = respx.get(
            "https://api.github.com/repos/devansh/test/languages"
        )

        route.side_effect = [
            httpx.Response(500),
            httpx.Response(
                200,
                json={"Python": 1000, "C++": 500},
            ),
        ]

        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(5)

            result = await fetch_repository_languages(
                repo,
                semaphore,
                client,
            )

            assert result == {"Python": 1000, "C++": 500}
            assert len(respx.calls) == 2

@pytest.mark.asyncio
async def test_fetch_all_repositories_server_error(monkeypatch):
       repo = {
       "languages_url": "https://api.github.com/repos/devansh/test/languages"
       }

       async def fake_sleep(delay):
           pass

       monkeypatch.setattr(asyncio,"sleep",fake_sleep)

       with respx.mock:
          route = respx.get("https://api.github.com/repos/devansh/test/languages")
          route.side_effect = [
              httpx.Response(500),
              httpx.Response(500),
              httpx.Response(500)
              ]
       

          async with httpx.AsyncClient() as client:
               semaphore = asyncio.Semaphore(5)
               with pytest.raises(GithubServerError):
                    await fetch_repository_languages(
                      repo,
                      semaphore,
                      client
                     )

          assert len(respx.calls)==3
                 
    
@pytest.mark.asyncio
async def test_fetch_repository_languages_timeout():
    repo = {
        "languages_url": "https://api.github.com/repos/devansh/test/languages"
    }

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(5)

        with respx.mock:
            respx.get(
                "https://api.github.com/repos/devansh/test/languages"
            ).mock(
                side_effect=httpx.ReadTimeout("GitHub timed out")
            )

            result = await fetch_repository_languages(
                repo,
                semaphore,
                client,
            )

    assert result is None


@pytest.mark.asyncio
async def test_partial_failure(monkeypatch):

    repos = [
        {"languages_url": "repo-a"},
        {"languages_url": "repo-b"},
        {"languages_url": "repo-c"},
    ]

    async def fake_fetch(repo, semaphore, client):

        if repo["languages_url"] == "repo-b":
            return None       # simulate timeout

        return {"Python": 100}

    monkeypatch.setattr(
        "app.github_service.fetch_repository_languages",
        fake_fetch
    )

    async with httpx.AsyncClient() as client:
        result = await fetch_all_repository_languages(
            repos,
            client
        )

    assert len(result) == 2
    assert result == [
    {"Python": 100},
    {"Python": 100},
]


@pytest.mark.asyncio
async def test_max_concurrent_github_requests():

    repos = [
        {
            "languages_url":
                f"https://api.github.com/repos/devansh/repo{i}/languages",
            "fork": False,
            "archived": False,
        }
        for i in range(10)
    ]

    current_running = 0
    max_running = 0
    MAX_CONCURRENT_GITHUB_REQUESTS = 5
    async def mock_response(request):
        nonlocal current_running, max_running

        current_running += 1
        max_running = max(max_running, current_running)

        await asyncio.sleep(0.01)

        current_running -= 1

        return httpx.Response(
            200,
            json={"Python": 100}
        )

    with respx.mock:
        route = respx.get(
            url__regex=r"https://api\.github\.com/repos/devansh/repo\d+/languages"
        )

        route.side_effect = mock_response

        async with httpx.AsyncClient() as client:
            result = await fetch_all_repository_languages(
                repos,
                client
            )

    assert len(result) == 10
    assert max_running <= MAX_CONCURRENT_GITHUB_REQUESTS
    
