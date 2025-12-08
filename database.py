
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb+srv://trivedidevansh1080_db_user:Q2jlFgyFLnnyq7px@githubstats.16hgp0d.mongodb.net/?appName=GithubStats"

client = AsyncIOMotorClient(MONGO_URL)
db = client["github_stats_db"]       # database name
stats_collection = db["stats"]       # collection name
