from fastapi import APIRouter, HTTPException
import json, time
from storage import json_store
from websocket.manager import manager
from redis_state.buzzer import get_winner
from models.schemas import ScoreCorrectRequest

router = APIRouter(tags=["scores"])

def _events(): return json_store.load("events", {})
def _teams(): return json_store.load("teams", {})
def _rounds(): return json_store.load("rounds", {})
def _participants(): return json_store.load("participants", {})
def _results(): return json_store.load("results", [])

def _event_teams(teams, event_id):
    return [dict(t) for t in teams.values() if t.get("event_id") == event_id]

@router.post("/api/events/{event_id}/score/correct")
async def mark_correct(event_id: str, payload: ScoreCorrectRequest):
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
    # get winner
    winner_raw = await get_winner(rid)
    if not winner_raw:
        # try from rnd
        if rnd.get("winner"):
            winner = rnd["winner"]
        else:
            raise HTTPException(status_code=400, detail="No winner to award")
    else:
        try:
            winner = json.loads(winner_raw)
        except:
            winner = winner_raw if isinstance(winner_raw, dict) else {}
    team_id = winner.get("team_id") or winner.get("teamId")
    if not team_id:
        raise HTTPException(status_code=400, detail="Winner has no team")
    # Scoring is a one-time action per round; check before changing the score.
    if any(r.get("round_id") == rid for r in _results()):
        raise HTTPException(status_code=409, detail="Round already scored")
    if team_id not in _teams():
        raise HTTPException(status_code=404, detail="Team not found")
    updated_team, teams = json_store.adjust_team_score(team_id, payload.points)
    if updated_team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    # persist result
    results = _results()
    results.append({
        "round_id": rid,
        "event_id": event_id,
        "question_id": ev.get("current_question_id"),
        "participant_id": winner.get("participant_id"),
        "participant_name": winner.get("participant_name"),
        "team_id": team_id,
        "team_name": winner.get("team_name"),
        "points": payload.points,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "correct": True
    })
    json_store.save("results", results)
    # update round
    rnd["status"] = "COMPLETED"
    rounds[rid] = rnd
    json_store.save("rounds", rounds)
    await manager.broadcast(ev["code"], {"type": "SCORE_UPDATED", "team_id": team_id, "score": updated_team["score"], "teams": _event_teams(teams, event_id)})
    await manager.broadcast(ev["code"], {"type": "ANSWER_RESULT", "correct": True, "team_id": team_id, "points": payload.points})
    return {"ok": True, "team": updated_team}

@router.post("/api/events/{event_id}/score/wrong")
async def mark_wrong(event_id: str, payload: ScoreCorrectRequest | None = None):
    points = payload.points if payload is not None else -10
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
    if any(r.get("round_id") == rid for r in _results()):
        raise HTTPException(status_code=409, detail="Round already scored")
    winner_raw = await get_winner(rid)
    winner = None
    if winner_raw:
        try:
            winner = json.loads(winner_raw)
        except:
            winner = {}
    else:
        winner = rnd.get("winner")
    if not winner:
        raise HTTPException(status_code=400, detail="No winner to score")
    team_id = winner.get("team_id") or winner.get("teamId")
    if not team_id or team_id not in _teams():
        raise HTTPException(status_code=404, detail="Winner team not found")
    updated_team, teams = json_store.adjust_team_score(team_id, points)
    if updated_team is None:
        raise HTTPException(status_code=404, detail="Winner team not found")
    # Persist the configured negative/positive wrong-answer points.
    results = _results()
    results.append({
        "round_id": rid,
        "event_id": event_id,
        "question_id": ev.get("current_question_id"),
        "participant_id": winner.get("participant_id") if winner else None,
        "participant_name": winner.get("participant_name") if winner else None,
        "team_id": team_id,
        "team_name": winner.get("team_name") if winner else None,
        "points": points,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "correct": False
    })
    json_store.save("results", results)
    rnd["status"] = "COMPLETED"
    rounds[rid] = rnd
    json_store.save("rounds", rounds)
    await manager.broadcast(ev["code"], {"type": "SCORE_UPDATED", "team_id": team_id, "score": updated_team["score"], "teams": _event_teams(teams, event_id)})
    await manager.broadcast(ev["code"], {"type": "ANSWER_RESULT", "correct": False, "team_id": team_id, "points": points})
    return {"ok": True, "team": updated_team}

@router.get("/api/events/{event_id}/leaderboard")
def leaderboard(event_id: str):
    events = _events()
    ev = None
    for v in events.values():
        if v["id"] == event_id or v["code"] == event_id:
            ev = v
            event_id = v["id"]
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    teams = _teams()
    lst = [t for t in teams.values() if t["event_id"] == event_id]
    lst.sort(key=lambda x: x.get("score", 0), reverse=True)
    out = []
    for i, t in enumerate(lst, start=1):
        out.append({"rank": i, "team_id": t["id"], "team_name": t["name"], "score": t.get("score", 0)})
    # individual buzzer stats
    results = _results()
    # count winning buzzes per participant
    from collections import Counter
    c = Counter()
    for r in results:
        if r.get("event_id") == event_id and r.get("participant_id"):
            c[(r.get("participant_name"), r.get("team_name"))] += 1
    top = [{"name": k[0], "team": k[1], "wins": v} for k, v in c.most_common(5)]
    return {"teams": out, "top_buzzers": top}

@router.get("/api/events/{event_id}/results")
def results(event_id: str):
    events = _events()
    for v in events.values():
        if v["id"] == event_id or v["code"] == event_id:
            event_id = v["id"]
            break
    else:
        raise HTTPException(status_code=404, detail="Event not found")
    all_res = _results()
    return [r for r in all_res if r.get("event_id") == event_id]
