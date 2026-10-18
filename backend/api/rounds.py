from fastapi import APIRouter, HTTPException
import uuid, time, json
from storage import json_store
from redis_state.buzzer import set_round_status, get_round_status, get_winner, clear_round, set_event_round
from websocket.manager import manager
from models.schemas import RoundStatus

router = APIRouter(tags=["rounds"])

def _events():
    return json_store.load("events", {})
def _questions():
    return json_store.load("questions", {})
def _rounds():
    return json_store.load("rounds", {})
def _save_events(d): json_store.save("events", d)
def _save_rounds(d): json_store.save("rounds", d)

def _resolve_event(event_id: str):
    events = _events()
    for k, v in events.items():
        if v["id"] == event_id or v["code"] == event_id:
            return v, k, v["id"], events
    raise HTTPException(status_code=404, detail="Event not found")

def _qlist(event_id: str):
    questions = _questions()
    return sorted([q for q in questions.values() if q["event_id"] == event_id], key=lambda x: x["number"])

def _qpos(qlist, qid):
    return next((i for i, q in enumerate(qlist) if q["id"] == qid), -1)

async def _make_round(ev, ev_key, events, question):
    rounds = _rounds()
    rid = "r_" + uuid.uuid4().hex[:8]
    rnd = {
        "id": rid,
        "event_id": ev["id"],
        "question_id": question["id"],
        "status": RoundStatus.QUESTION_ACTIVE.value,
        "winner": None,
        "created_at": time.time()
    }
    rounds[rid] = rnd
    _save_rounds(rounds)
    ev["current_round_id"] = rid
    ev["current_question_id"] = question["id"]
    ev["que_over"] = False
    ev["status"] = "RUNNING"
    events[ev_key] = ev
    _save_events(events)
    await set_round_status(rid, RoundStatus.QUESTION_ACTIVE.value)
    await set_event_round(ev["code"], rid)
    await manager.broadcast(ev["code"], {"type": "QUESTION_STARTED", "round_id": rid, "question": question})
    await manager.broadcast(ev["code"], {"type": "ROUND_STATE", "round": rnd, "question": question})
    return {"round": rnd, "question": question, "que_over": False}

@router.post("/api/events/{event_id}/round/start")
async def start_round(event_id: str):
    ev, ev_key, eid, events = _resolve_event(event_id)
    qlist = _qlist(eid)
    if not qlist:
        raise HTTPException(status_code=400, detail="No questions")
    current_qid = ev.get("current_question_id")
    if current_qid is None:
        return await _make_round(ev, ev_key, events, qlist[0])
    idx = _qpos(qlist, current_qid)
    if idx == -1:
        return await _make_round(ev, ev_key, events, qlist[0])
    if idx + 1 < len(qlist):
        return await _make_round(ev, ev_key, events, qlist[idx + 1])
    raise HTTPException(status_code=400, detail="No more questions")

@router.post("/api/events/{event_id}/round/open-buzzer")
async def open_buzzer(event_id: str):
    ev, _, eid, _events_all = _resolve_event(event_id)
    if ev.get("que_over"):
        raise HTTPException(status_code=400, detail="Que over")
    rid = ev.get("current_round_id")
    if not rid:
        raise HTTPException(status_code=400, detail="No active round")
    rounds = _rounds()
    rnd = rounds.get(rid)
    if not rnd:
        raise HTTPException(status_code=404, detail="Round not found")
    rnd["status"] = RoundStatus.BUZZER_OPEN.value
    rounds[rid] = rnd
    _save_rounds(rounds)
    await set_round_status(rid, RoundStatus.BUZZER_OPEN.value)
    await clear_round(rid)  # ensure winner cleared before opening? But need to keep status OPEN
    await set_round_status(rid, RoundStatus.BUZZER_OPEN.value)
    await manager.broadcast(ev["code"], {"type": "BUZZER_OPEN", "round_id": rid})
    return {"ok": True, "round_id": rid}

@router.post("/api/events/{event_id}/round/reset")
async def reset_buzzer(event_id: str):
    ev, _, _eid, _all = _resolve_event(event_id)
    rid = ev.get("current_round_id")
    if not rid:
        raise HTTPException(status_code=400, detail="No active round")
    rounds = _rounds()
    if rid in rounds:
        rounds[rid]["status"] = RoundStatus.WAITING.value
        rounds[rid]["winner"] = None
        _save_rounds(rounds)
    await clear_round(rid)
    await set_round_status(rid, RoundStatus.WAITING.value)
    await manager.broadcast(ev["code"], {"type": "ROUND_RESET", "round_id": rid})
    await manager.broadcast(ev["code"], {"type": "BUZZER_CLOSED"})
    return {"ok": True}

@router.post("/api/events/{event_id}/round/next")
async def next_question(event_id: str):
    # Mark current round completed then start next.
    # If the current question was the last one, latch Que Over instead of erroring silently.
    ev, ev_key, eid, events = _resolve_event(event_id)
    qlist = _qlist(eid)
    if not qlist:
        raise HTTPException(status_code=400, detail="No questions")
    rid = ev.get("current_round_id")
    if rid:
        rounds = _rounds()
        if rid in rounds:
            rounds[rid]["status"] = RoundStatus.COMPLETED.value
            _save_rounds(rounds)
            await set_round_status(rid, RoundStatus.COMPLETED.value)
    current_qid = ev.get("current_question_id")
    if current_qid is None:
        return await _make_round(ev, ev_key, events, qlist[0])
    idx = _qpos(qlist, current_qid)
    if idx == -1:
        return await _make_round(ev, ev_key, events, qlist[0])
    if idx + 1 < len(qlist):
        return await _make_round(ev, ev_key, events, qlist[idx + 1])
    # no more questions -> Que Over
    ev["que_over"] = True
    events[ev_key] = ev
    _save_events(events)
    await manager.broadcast(ev["code"], {"type": "QUE_OVER"})
    return {"que_over": True, "round": None, "question": None}

@router.post("/api/events/{event_id}/round/prev")
async def prev_question(event_id: str):
    ev, ev_key, eid, events = _resolve_event(event_id)
    qlist = _qlist(eid)
    if not qlist:
        raise HTTPException(status_code=400, detail="No questions")
    current_qid = ev.get("current_question_id")
    if current_qid is None:
        raise HTTPException(status_code=400, detail="No active question")
    idx = _qpos(qlist, current_qid)
    if idx == -1:
        return await _make_round(ev, ev_key, events, qlist[0])
    if idx <= 0:
        raise HTTPException(status_code=400, detail="Already at first question")
    # mark current completed, go back one
    rid = ev.get("current_round_id")
    if rid:
        rounds = _rounds()
        if rid in rounds:
            rounds[rid]["status"] = RoundStatus.COMPLETED.value
            _save_rounds(rounds)
            await set_round_status(rid, RoundStatus.COMPLETED.value)
    return await _make_round(ev, ev_key, events, qlist[idx - 1])

@router.get("/api/events/{event_id}/round/state")
async def round_state(event_id: str):
    ev, _, eid, _all = _resolve_event(event_id)
    qlist = _qlist(eid)
    total = len(qlist)
    current_qid = ev.get("current_question_id")
    idx = _qpos(qlist, current_qid) if current_qid else -1
    base = {
        "que_over": bool(ev.get("que_over", False)),
        "total_questions": total,
        "question_index": (idx + 1) if idx >= 0 else 0,
        "is_first": idx <= 0,
        "is_last": idx >= 0 and idx == total - 1,
    }
    rid = ev.get("current_round_id")
    if not rid:
        return {"round": None, "question": None, "winner": None, "buzzer_status": "WAITING", **base}
    rounds = _rounds()
    rnd = rounds.get(rid)
    questions = _questions()
    q = questions.get(current_qid) if current_qid else None
    # winner from redis
    winner_raw = await get_winner(rid)
    winner = None
    if winner_raw:
        try:
            winner = json.loads(winner_raw)
        except:
            winner = winner_raw
    # also from rounds storage if redis empty
    if not winner and rnd and rnd.get("winner"):
        winner = rnd["winner"]
    status = await get_round_status(rid) or (rnd.get("status") if rnd else "WAITING")
    return {"round": rnd, "question": q, "winner": winner, "buzzer_status": status, **base}
