import redis.asyncio as redis
import os
import json
import fnmatch

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class InMemoryRedisClient:
    """로컬 Redis 서버가 오프라인일 때 대신 메모리에 데이터를 보관해 주는 폴백 캐시 클라이언트.

    데모/오프라인 환경에서 실제 Redis 없이도 동작하도록, 세션이 사용하는 명령
    (rpush/lrange/get/set/keys/delete/expire)을 모두 지원한다.
    """
    def __init__(self):
        self.store = {}

    async def ping(self):
        return True

    # --- List 계열 (읽기 이벤트 버퍼) ---
    async def rpush(self, key: str, value: str):
        if not isinstance(self.store.get(key), list):
            self.store[key] = []
        self.store[key].append(value)
        return len(self.store[key])

    async def lrange(self, key: str, start: int, end: int):
        lst = self.store.get(key, [])
        if not isinstance(lst, list):
            return []
        if end == -1:
            return lst[start:]
        return lst[start:end + 1]

    # --- String 계열 (퀴즈 채점 누적 등) ---
    async def get(self, key: str):
        v = self.store.get(key)
        return v if isinstance(v, str) or v is None else None

    async def set(self, key: str, value: str, ex: int | None = None, **kwargs):
        # ex(만료)는 인메모리에선 무시(데모 수명 내 유지)
        self.store[key] = value
        return True

    async def keys(self, pattern: str = "*"):
        return [k for k in list(self.store.keys()) if fnmatch.fnmatch(k, pattern)]

    async def delete(self, key: str):
        if key in self.store:
            del self.store[key]
            return 1
        return 0

    async def expire(self, key: str, seconds: int):
        return True

    async def aclose(self):
        # 공유 싱글턴이므로 실제로 닫지 않는다(인메모리는 no-op).
        pass

_redis_client = None
_redis_offline = False

async def get_redis():
    """단일 공유 클라이언트를 반환한다(실제 Redis 또는 InMemory 폴백 싱글턴).

    이전 구현은 오프라인일 때 매 호출마다 새 InMemoryRedisClient()를 만들어
    요청 간 데이터(퀴즈 채점 누적 등)가 공유되지 않았다. 반드시 싱글턴을 반환한다.
    """
    global _redis_client, _redis_offline

    if _redis_client is not None:
        return _redis_client

    try:
        # 1. 실제 Redis 클라이언트 연결 시도
        raw_client = redis.from_url(REDIS_URL, decode_responses=True)
        await raw_client.ping()  # ping 테스트
        _redis_client = raw_client
        print("[Redis] Local Redis server connection successful.")
    except Exception as e:
        # 2. 연결 실패 시 InMemory 폴백 싱글턴으로 전환
        print(f"[Redis] Local Redis server is offline ({e}). Using InMemory Cache Fallback.")
        _redis_offline = True
        _redis_client = InMemoryRedisClient()

    return _redis_client
