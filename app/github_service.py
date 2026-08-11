import asyncio
import httpx

from .github_api import fetch_from_github


# Reuse one HTTP client for GitHub API requests.
# We will revisit client lifecycle later when we productionize the app.
client = httpx.AsyncClient()

MAX_CONCURRENT_GITHUB_REQUESTS = 5
MAX_REPO_SIZE_TO_CONSIDER = 5_000_000


async def get_user_repositories(username: str) -> list[dict]:
    """
    Fetch repositories belonging to a GitHub user.

    Returns:
        A list of repository dictionaries returned by GitHub.
    """

    repo_url = f"https://api.github.com/users/{username}/repos"

    repos = await fetch_from_github(repo_url)

    return repos


async def fetch_repository_languages(
    repo: dict,
    semaphore: asyncio.Semaphore,
) -> dict | None:
    """
    Fetch language statistics for one GitHub repository.

    Returns:
        A dictionary containing language names and byte counts,
        or None if this repository cannot be processed.
    """

    # GitHub provides the exact endpoint for this repository.
    lang_url = repo["languages_url"]

    try:
        # Only MAX_CONCURRENT_GITHUB_REQUESTS coroutines
        # can enter this block at the same time.
        async with semaphore:

            # Make the HTTP request to GitHub.
            response = await client.get(lang_url)

            # Raise an exception for unsuccessful HTTP responses.
            response.raise_for_status()

            # Convert the JSON response into a Python object.
            lang_data = response.json()

            # The languages endpoint should return a non-empty dictionary.
            if not isinstance(lang_data, dict) or not lang_data:
                raise ValueError("Invalid language data returned by GitHub")

            # Every language's value should be an integer byte count.
            if not all(isinstance(value, int) for value in lang_data.values()):
                raise ValueError(
                    "Invalid language byte counts returned by GitHub"
                )
            total_bytes = sum(lang_data.values())
            if total_bytes> MAX_REPO_SIZE_TO_CONSIDER:
                raise ValueError(
                     "Large size repository"
                )

            return lang_data

    except (httpx.HTTPError, ValueError):
        # One repository failing should not fail the entire request.
        return None


async def fetch_all_repository_languages(
    repos: list[dict],
) -> list[dict]:
    """
    Fetch language statistics for all valid repositories
    using bounded concurrency.
    """

    # Controls the maximum number of GitHub requests
    # that can be active simultaneously.
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_GITHUB_REQUESTS)

    coroutines = []

    for repo in repos:

        # Skip forked repositories.
        if repo.get("fork"):
            continue

        # Skip archived repositories.
        if repo.get("archived"):
            continue

        # Create the coroutine but do not await it yet.
        coroutines.append(
            fetch_repository_languages(repo, semaphore)
        )

    # Run the repository-fetching coroutines concurrently.
    # The semaphore inside each coroutine limits the actual
    # number of simultaneous GitHub requests.
    all_languages = await asyncio.gather(*coroutines)

    # Remove repositories whose language request failed.
    all_languages = [
        result
        for result in all_languages
        if result is not None
    ]

    return all_languages
