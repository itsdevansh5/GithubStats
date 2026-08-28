import asyncio
import httpx

from .github_api import fetch_from_github
from .exceptions import GithubRateLimitError,GithubServerError

# Reuse one HTTP client for GitHub API requests.





MAX_CONCURRENT_GITHUB_REQUESTS = 5
MAX_REPO_SIZE_TO_CONSIDER = 5_000_000
MAX_ATTEMPTS = 3

def get_next_url(link_header:str | None) -> str | None:
    if not link_header:
       return None

    links =  link_header.split(',')
    for link in links:
       if 'rel="next"' in link:
          return link.strip().split(';')[0].strip('<>')
   
    return None


async def get_user_repositories(username: str,client : httpx.AsyncClient) -> list[dict]:
    """
    Fetch repositories belonging to a GitHub user.

    Returns:
        A list of repository dictionaries returned by GitHub.
    """
    repos = []
    repo_url = f"https://api.github.com/users/{username}/repos?per_page=100"
   
    while repo_url:
        repos_one_page,link = await fetch_from_github(repo_url,client)
        repos.extend(repos_one_page)
        repo_url = get_next_url(link)
      
    return repos
   
    
     
 
async def fetch_repository_languages(
    repo: dict,
    semaphore: asyncio.Semaphore,
    client: httpx.AsyncClient
) -> dict | None:
    """
    Fetch language statistics for one GitHub repository.

    Returns:
        A dictionary containing language names and byte counts,
        or None if this repository cannot be processed.
    """

    # GitHub provides the exact endpoint for this repository.
    lang_url = repo["languages_url"]
    
    for attempt in range(MAX_ATTEMPTS):
        
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
    
        except httpx.TimeoutException:
            return None

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code==429:
                raise GithubRateLimitError("Github Rate limit has been exceeded")

            if 500<=exc.response.status_code<600:
                if attempt<MAX_ATTEMPTS-1:
                     await asyncio.sleep(2**attempt)
                     continue
                raise GithubServerError("Github Internal Server Error")
        
            return None

        except (httpx.HTTPError, ValueError):
        # One repository failing should not fail the entire request.
            return None


async def fetch_all_repository_languages(
    repos: list[dict],
    client: httpx.AsyncClient
) -> list[dict]:
    """
    Fetch language statistics for all valid repositories
    using bounded concurrency.
    """

    # Controls the maximum number of GitHub requests
    # that can be active simultaneously.
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_GITHUB_REQUESTS)

    tasks = []

    for repo in repos:

        # Skip forked repositories.
        if repo.get("fork"):
            continue

        # Skip archived repositories.
        if repo.get("archived"):
            continue

        # Create the coroutine but do not await it yet.
        tasks.append(
           asyncio.create_task(fetch_repository_languages(repo, semaphore,client))
        )
    # Created tasks instead of coroutines to get control for cancellation when needed
    # Run the repository-fetching tasks concurrently.
    # The semaphore inside each coroutine limits the actual
    # number of simultaneous GitHub requests.
    try:
         all_languages = await asyncio.gather(*tasks)
    
    except (GithubRateLimitError,GithubServerError):
        for task in tasks:
           if not task.done():
               task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        raise

    # Remove repositories whose language request failed.
    all_languages = [
        result
        for result in all_languages
        if result is not None
    ]

    return all_languages
    
