import os
import redis.asyncio as redis
from .config import settings



def create_redis_client():
    return redis.from_url(
            settings.redis_url,
            decode_responses=True
           )

