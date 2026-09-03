import time
from .client import get_redis, fallback_set_nx, fallback_get, fallback_delete

ROUND_STATUS_KEY = "round:{rid}:status"
ROUND_WINNER_KEY = "round:{rid}:winner"
EVENT_ROUND_KEY = "event:{code}:current_round"
EVENT_STATUS_KEY = "event:{code}:buzzer_status"

async def set_round_status(round_id: str, status: str):
    r = await get_redis()
    key = ROUND_STATUS_KEY.format(rid=round_id)
    if r:
        await r.set(key, status, ex=3600)
    else:
        from .client import _fallback_store
        _fallback_store[key] = status

async def get_round_status(round_id: str):
    r = await get_redis()
    key = ROUND_STATUS_KEY.format(rid=round_id)
    if r:
        return await r.get(key)
    else:
        return await fallback_get(key)

async def try_claim_winner(round_id: str, participant_payload: str) -> bool:
    """Atomic SET NX - returns True if this caller wins"""
    r = await get_redis()
    key = ROUND_WINNER_KEY.format(rid=round_id)
    if r:
        # SET NX with expiry
        result = await r.set(key, participant_payload, nx=True, ex=3600)
        return bool(result)
    else:
        return await fallback_set_nx(key, participant_payload, ttl=3600)

async def get_winner(round_id: str):
    r = await get_redis()
    key = ROUND_WINNER_KEY.format(rid=round_id)
    if r:
        return await r.get(key)
    else:
        return await fallback_get(key)

async def clear_round(round_id: str):
    r = await get_redis()
    wk = ROUND_WINNER_KEY.format(rid=round_id)
    sk = ROUND_STATUS_KEY.format(rid=round_id)
    if r:
        await r.delete(wk, sk)
    else:
        from .client import _fallback_store
        _fallback_store.pop(wk, None)
        _fallback_store.pop(sk, None)

async def set_event_round(event_code: str, round_id: str):
    r = await get_redis()
    key = EVENT_ROUND_KEY.format(code=event_code)
    if r:
        await r.set(key, round_id, ex=7200)
    else:
        from .client import _fallback_store
        _fallback_store[key] = round_id

async def get_event_round(event_code: str):
    r = await get_redis()
    key = EVENT_ROUND_KEY.format(code=event_code)
    if r:
        return await r.get(key)
    else:
        return await fallback_get(key)
