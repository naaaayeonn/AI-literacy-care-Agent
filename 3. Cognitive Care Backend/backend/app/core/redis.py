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

    async def exists(self, key: str) -> int:
        return 1 if key in self.store else 0

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
    자가 치유(Self-healing) 기능이 있어, 일시적인 연결 장애로 인메모리 폴백으로
    전환되었더라도 다음 호출 시 실제 Redis 서버와의 재연결을 시도한다.
    """
    global _redis_client, _redis_offline

    if _redis_client is not None and not _redis_offline:
        return _redis_client

    try:
        # 실제 Redis 클라이언트 연결 시도
        raw_client = redis.from_url(
            REDIS_URL, 
            decode_responses=True, 
            max_connections=5, 
            health_check_interval=10
        )
        await raw_client.ping()  # ping 테스트
        
        # 연결 성공 시 실제 Redis로 전환
        _redis_client = raw_client
        _redis_offline = False
        print("[Redis] Redis server connection successful.")
    except Exception as e:
        # 연결 실패 시 이미 생성된 인메모리 싱글턴이 있으면 그것을 반환
        if _redis_client is not None:
            return _redis_client
            
        print(f"[Redis] Redis connection failed ({e}). Using InMemory Fallback.")
        _redis_offline = True
        _redis_client = InMemoryRedisClient()

    return _redis_client

    return _redis_client
