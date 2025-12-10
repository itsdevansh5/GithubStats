
import httpx
from fastapi import HTTPException
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

async def fetch_from_github(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="GitHub API error or user not found"
        )
    return response.json()

print("TOKEN USED:", os.getenv("GITHUB_TOKEN"))
