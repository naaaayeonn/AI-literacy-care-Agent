import redis.asyncio as redis
import os
import asyncio

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 로컬 메모리 캐시 (Redis가 오프라인일 때 사용할 fallback 버퍼)
_IN_MEMORY_CACHE: dict[str, list[str]] = {}

class InMemoryRedisClient:
    """Redis가 연결되지 않았을 때 대신 동작하는 메모리 에뮬레이터."""
    
    async def ping(self):
        return True
        
    async def rpush(self, key: str, value: str):
        if key not in _IN_MEMORY_CACHE:
            _IN_MEMORY_CACHE[key] = []
        _IN_MEMORY_CACHE[key].append(value)
        return len(_IN_MEMORY_CACHE[key])
        
    async def lrange(self, key: str, start: int, end: int):
        lst = _IN_MEMORY_CACHE.get(key, [])
        if not lst:
            return []
        # Python 슬라이스 매핑 (end가 -1일 때 대응)
        if end == -1:
            return lst[start:]
        return lst[start:end+1]
        
    async def expire(self, key: str, seconds: int):
        return True
        
    async def delete(self, key: str):
        if key in _IN_MEMORY_CACHE:
            del _IN_MEMORY_CACHE[key]
            return 1
        return 0
        
    async def aclose(self):
        pass


async def get_redis() -> redis.Redis | InMemoryRedisClient:
    """Redis 연결을 시도하고, 실패 시 로컬 InMemoryRedisClient를 반환합니다."""
    client = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        # 연결 가능 여부 검증 (짧은 타임아웃 테스트)
        await asyncio.wait_for(client.ping(), timeout=1.0)
        return client
    except Exception as e:
        print(f"[Redis] Local Redis server is offline ({e}). Using InMemory Cache Fallback.")
        await client.aclose()
        return InMemoryRedisClient()

