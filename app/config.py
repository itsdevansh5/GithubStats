import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
REDIS_URL = os.getenv("REDIS_URL")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
