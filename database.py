
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

client = AsyncIOMotorClient(MONGO_URL)
db = client["github_stats_db"]       # database name
stats_collection = db["stats"]# collection name
history_collection = db["history"] #for snapshots

