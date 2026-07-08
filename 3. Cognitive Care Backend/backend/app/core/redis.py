import redis.asyncio as redis
import os
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class InMemoryRedisClient:
    """로컬 Redis 서버가 오프라인일 때 대신 메모리에 데이터를 보관해 주는 폴백 캐시 클라이언트"""
    def __init__(self):
        self.store = {}

    async def ping(self):
        return True

    async def rpush(self, key: str, value: str):
        if key not in self.store:
            self.store[key] = []
        self.store[key].append(value)
        return len(self.store[key])

    async def lrange(self, key: str, start: int, end: int):
        lst = self.store.get(key, [])
        if end == -1:
            return lst[start:]
        return lst[start:end+1]

    async def delete(self, key: str):
        if key in self.store:
            del self.store[key]
            return 1
        return 0

    async def expire(self, key: str, seconds: int):
        return True

    async def aclose(self):
        pass

_redis_client = None
_redis_offline = False

async def get_redis():
    global _redis_client, _redis_offline
    
    # 이미 오프라인이 확인되어 InMemory로 전환된 경우 즉각 폴백 반환
    if _redis_offline:
        return InMemoryRedisClient()

    if _redis_client is None:
        try:
            # 1. 실제 Redis 클라이언트 연결 시도
            raw_client = redis.from_url(REDIS_URL, decode_responses=True)
            # 2. ping 테스트 (1초 타임아웃)
            await raw_client.ping()
            _redis_client = raw_client
            print("[Redis] Local Redis server connection successful.")
        except Exception as e:
            # 3. 연결 실패 시 InMemory 폴백으로 전면 전환
            print(f"[Redis] Local Redis server is offline ({e}). Using InMemory Cache Fallback.")
            _redis_offline = True
            _redis_client = InMemoryRedisClient()

    return _redis_client
