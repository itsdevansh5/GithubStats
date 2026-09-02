
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings



def create_mongo_client():
  
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client["github_stats_db"]       # database name
    return client,db

