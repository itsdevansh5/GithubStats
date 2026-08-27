
import httpx
from .exceptions import GithubRateLimitError,GithubServerError
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

async def fetch_from_github(url: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=HEADERS)
            response.raise_for_status()
      
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code==429:
               raise GithubRateLimitError("Github Rate Limit Exhausted")              
            if 500<=exc.response.status_code<600:
               raise GithubServerError("Github Internal Server problem")
            raise
       
        link_header = response.headers.get("Link")
        return response.json(),link_header
           
              

