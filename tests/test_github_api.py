from app.github_service import get_next_url
from app.github_service import get_user_repositories
import httpx
import respx
import pytest
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
            assert len(respx.calls) == 2
