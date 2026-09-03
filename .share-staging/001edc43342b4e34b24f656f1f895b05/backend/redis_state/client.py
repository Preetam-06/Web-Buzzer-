import asyncio, time
from config.settings import settings

_redis = None
_redis_available = None  # None=unknown, True=ok, False=failed
_redis_retry_after = 0.0
_fallback_store = {}
_fallback_lock = asyncio.Lock()

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

async def get_redis():
    global _redis, _redis_available, _redis_retry_after
    if not HAS_REDIS:
        _redis_available = False
        return None
    # Do not block every request with a connection timeout when Redis is down.
    now = time.monotonic()
    if _redis_available is False and now < _redis_retry_after:
        return None
    if _redis is not None:
        _redis_available = True
        return _redis
    try:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)
        await _redis.ping()
        if _redis_available is not True:
            print(f"[Redis] Connected to {settings.REDIS_URL} - READY for 50+ players")
        _redis_available = True
        _redis_retry_after = 0.0
        return _redis
    except Exception as e:
        if _redis_available is not False:
            print(f"[Redis] NOT available at {settings.REDIS_URL}: {e}")
            print(f"[Redis] FALLBACK in-memory active (OK for testing <50, NOT safe for >50 concurrent buzz!)")
        _redis = None
        _redis_available = False
        _redis_retry_after = time.monotonic() + 5.0
        return None

def is_redis_available() -> bool | None:
    return _redis_available

# Fallback in-memory atomic SET NX
async def fallback_set_nx(key: str, value: str, ttl: int = 3600) -> bool:
    async with _fallback_lock:
        if key in _fallback_store:
            return False
        _fallback_store[key] = value
        return True

async def fallback_get(key: str):
    return _fallback_store.get(key)

async def fallback_delete(key: str):
    async with _fallback_lock:
        _fallback_store.pop(key, None)
        # delete related keys pattern simulation
        to_del = [k for k in list(_fallback_store.keys()) if k.startswith(key)]
        for k in to_del:
            _fallback_store.pop(k, None)

async def fallback_exists(key: str) -> bool:
    return key in _fallback_store
