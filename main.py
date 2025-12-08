
from fastapi import *
import httpx

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to Github Stats API"}

@app.get("/hello/{name}")
def greet(name: str):
    return {"message": f"Hello {name}, welcome to the API!"}

async def fetch_from_github(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="GitHub API error or user not found"
        )

    return response.json()

async def get_repo_languages(languages_url: str):
    return await fetch_from_github(languages_url)

@app.get("/repos/{username}")
async def get_repos(username: str):
    url = f"https://api.github.com/users/{username}/repos"
    repos = await fetch_from_github(url)

    clean_data = [
        {
            "name": repo["name"],
            "url": repo["html_url"],
            "languages_url": repo["languages_url"]
        }
        for repo in repos
    ]

    return clean_data

@app.get("/stats/{username}")
async def get_language_stats(username: str):
    url = f"https://api.github.com/users/{username}/repos"
    repos = await fetch_from_github(url)

    total_langs = {}

    # fetch language data for each repo
    async with httpx.AsyncClient() as client:
        for repo in repos:
            lang_url = repo["languages_url"]
            response = await client.get(lang_url)
            lang_data = response.json()

            for lang, bytes_count in lang_data.items():
                total_langs[lang] = total_langs.get(lang, 0) + bytes_count

    # convert to percentages
    total_bytes = sum(total_langs.values())
    percentages = {
        lang: round((count / total_bytes) * 100, 2)
        for lang, count in total_langs.items()
    }

    return {
        "username": username,
        "total_bytes": total_langs,
        "percentages": percentages
    }
