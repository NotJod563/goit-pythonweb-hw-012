import json
from typing import Optional
from redis.asyncio import Redis
from app.config import settings

_redis: Optional[Redis] = None
USER_CACHE_TTL = 900  

async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

def _user_key(user_id: int) -> str:
    return f"user:{user_id}"

async def cache_user(user_id: int, payload: dict) -> None:
    r = await get_redis()
    await r.set(_user_key(user_id), json.dumps(payload), ex=USER_CACHE_TTL)

async def get_user_from_cache(user_id: int) -> Optional[dict]:
    r = await get_redis()
    raw = await r.get(_user_key(user_id))
    return json.loads(raw) if raw else None

async def drop_user_cache(user_id: int) -> None:
    r = await get_redis()
    await r.delete(_user_key(user_id))
