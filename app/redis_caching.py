import os
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL")

def create_redis_client():
    return redis.from_url(
            REDIS_URL,
            decode_responses=True
           )

