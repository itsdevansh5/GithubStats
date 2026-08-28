
import httpx
from .exceptions import GithubRateLimitError,GithubServerError


                  
async def fetch_from_github(url: str, client:httpx.AsyncClient):

        try:
            response = await client.get(url)
            response.raise_for_status()
      
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code==429:
               raise GithubRateLimitError("Github Rate Limit Exhausted")              
            if 500<=exc.response.status_code<600:
               raise GithubServerError("Github Internal Server problem")
            raise
       
        link_header = response.headers.get("Link")
        return response.json(),link_header
           
              

