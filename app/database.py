
from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGO_URL



def create_mongo_client():
  
    client = AsyncIOMotorClient(MONGO_URL)
    db = client["github_stats_db"]       # database name
    return client,db

