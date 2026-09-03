from fastapi import APIRouter, HTTPException
import uuid, time, json
from storage import json_store
from redis_state.buzzer import set_round_status, get_round_status, get_winner, clear_round, set_event_round, get_event_round
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

@router.post("/api/events/{event_id}/round/start")
async def start_round(event_id: str):
    events = _events()
    ev = None
    ev_key = None
    for k, v in events.items():
        if v["id"] == event_id or v["code"] == event_id:
            ev = v
            ev_key = k
            event_id = v["id"]
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    questions = _questions()
    # find next question not yet used? Simplest: use smallest number not yet completed
    rounds = _rounds()
    # Determine current question: if ev has current_question_id, move to next number
    qlist = sorted([q for q in questions.values() if q["event_id"] == event_id], key=lambda x: x["number"])
    if not qlist:
        raise HTTPException(status_code=400, detail="No questions")
    # if current_question_id exists, find next
    current_qid = ev.get("current_question_id")
    next_q = None
    if current_qid is None:
        next_q = qlist[0]
    else:
        # find index
        idx = next((i for i, q in enumerate(qlist) if q["id"] == current_qid), -1)
        if idx >= 0 and idx + 1 < len(qlist):
            next_q = qlist[idx+1]
        else:
            # if no next, stay or error - for MVP allow restart from first if completed all
            if idx == len(qlist)-1:
                raise HTTPException(status_code=400, detail="No more questions")
            next_q = qlist[0]
    rid = "r_" + uuid.uuid4().hex[:8]
    rnd = {
        "id": rid,
        "event_id": event_id,
        "question_id": next_q["id"],
        "status": RoundStatus.QUESTION_ACTIVE.value,
        "winner": None,
        "created_at": time.time()
    }
    rounds[rid] = rnd
    _save_rounds(rounds)
    ev["current_round_id"] = rid
    ev["current_question_id"] = next_q["id"]
    ev["status"] = "RUNNING"
    events[ev_key] = ev
    _save_events(events)
    await set_round_status(rid, RoundStatus.QUESTION_ACTIVE.value)
    await set_event_round(ev["code"], rid)
    await manager.broadcast(ev["code"], {"type": "QUESTION_STARTED", "round_id": rid, "question": next_q})
    await manager.broadcast(ev["code"], {"type": "ROUND_STATE", "round": rnd, "question": next_q})
    return {"round": rnd, "question": next_q}

@router.post("/api/events/{event_id}/round/open-buzzer")
async def open_buzzer(event_id: str):
    events = _events()
    ev = None
    for v in events.values():
        if v["id"] == event_id or v["code"] == event_id:
            ev = v
            event_id = v["id"]
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
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
    events = _events()
    ev = None
    for v in events.values():
        if v["id"] == event_id or v["code"] == event_id:
            ev = v
            event_id = v["id"]
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
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
    # Mark current round completed then start next
    events = _events()
    ev = None
    ev_key = None
    for k, v in events.items():
        if v["id"] == event_id or v["code"] == event_id:
            ev = v
            ev_key = k
            event_id = v["id"]
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    rid = ev.get("current_round_id")
    if rid:
        rounds = _rounds()
        if rid in rounds:
            rounds[rid]["status"] = RoundStatus.COMPLETED.value
            _save_rounds(rounds)
            await set_round_status(rid, RoundStatus.COMPLETED.value)
    # now start next
    return await start_round(event_id)

@router.get("/api/events/{event_id}/round/state")
async def round_state(event_id: str):
    events = _events()
    ev = None
    for v in events.values():
        if v["id"] == event_id or v["code"] == event_id:
            ev = v
            event_id = v["id"]
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    rid = ev.get("current_round_id")
    if not rid:
        return {"round": None, "question": None, "winner": None, "buzzer_status": "WAITING"}
    rounds = _rounds()
    rnd = rounds.get(rid)
    questions = _questions()
    q = questions.get(ev.get("current_question_id")) if ev.get("current_question_id") else None
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
    return {"round": rnd, "question": q, "winner": winner, "buzzer_status": status}
