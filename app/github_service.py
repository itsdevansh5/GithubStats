import httpx

from .github_api import fetch_from_github


# Reuse one HTTP client for GitHub API requests.
# We will revisit client lifecycle later when we productionize the app.
client = httpx.AsyncClient()


async def get_user_repositories(username: str) -> list[dict]:
    """
    Fetch repositories belonging to a GitHub user.

    Returns:
        A list of repository dictionaries returned by GitHub.
    """

    repo_url = f"https://api.github.com/users/{username}/repos"

    repos = await fetch_from_github(repo_url)

    return repos


async def fetch_repository_languages(repo: dict) -> dict:
    """
    Fetch language statistics for one GitHub repository.

    Args:
        repo: Repository dictionary returned by GitHub.

    Returns:
        Dictionary containing language names and their byte counts.

        Example:
        {
            "Python": 54231,
            "HTML": 12341,
            "CSS": 8421
        }

    Raises:
        ValueError: If GitHub returns an invalid language response.
        httpx.HTTPStatusError: If GitHub returns an unsuccessful
        HTTP status code.
    """

    # GitHub provides the exact endpoint for this repository.
    lang_url = repo["languages_url"]

    # Make the HTTP request.
    response = await client.get(lang_url)

    # Raise an exception for HTTP errors such as 403, 404, 500, etc.
    response.raise_for_status()

    # Convert the JSON response body into a Python object.
    lang_data = response.json()

    # The languages endpoint should return a non-empty dictionary.
    if not isinstance(lang_data, dict) or not lang_data:
        raise ValueError("Invalid language data returned by GitHub")

    # Language byte counts should be integers.
    if not all(isinstance(value, int) for value in lang_data.values()):
        raise ValueError("Invalid language byte counts returned by GitHub")

    return lang_data


async def fetch_all_repository_languages(
    repos: list[dict],
) -> list[dict]:
    """
    Fetch language statistics for all valid repositories.

    Currently this function performs requests sequentially.
    We will replace this with bounded concurrency later.

    Returns:
        A list containing one language dictionary per valid repository.
    """

    all_languages = []

    for repo in repos:

        # Forked repositories are not included in the statistics.
        if repo.get("fork"):
            continue

        # Archived repositories are not included in the statistics.
        if repo.get("archived"):
            continue

        try:
            # Fetch language statistics for this repository.
            repo_languages = await fetch_repository_languages(repo)

            # Store the language dictionary.
            all_languages.append(repo_languages)

        except (httpx.HTTPError, ValueError):
            # If one repository cannot be processed,
            # skip it instead of failing the entire request.
            continue

    return all_languages
