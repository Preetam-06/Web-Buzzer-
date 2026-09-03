from fastapi import APIRouter, HTTPException
import uuid
from models.schemas import ParticipantJoin, ParticipantOut
from storage import json_store

router = APIRouter(tags=["participants"])

def _events():
    return json_store.load("events", {})
def _teams():
    return json_store.load("teams", {})
def _participants():
    return json_store.load("participants", {})
def _save_parts(d):
    json_store.save("participants", d)

@router.post("/api/events/{event_code}/join", response_model=ParticipantOut)
def join_event(event_code: str, payload: ParticipantJoin):
    events = _events()
    ev = None
    for e in events.values():
        if e["code"] == event_code or e["id"] == event_code:
            ev = e
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Invalid event")
    # status check - allow CREATED etc? For MVP allow any except FINISHED
    if ev.get("status") == "FINISHED":
        raise HTTPException(status_code=400, detail="Event finished")
    teams = _teams()
    if payload.team_id not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    if teams[payload.team_id]["event_id"] != ev["id"]:
        raise HTTPException(status_code=400, detail="Team not in event")
    participants = _participants()
    # capacity check (backend enforcement)
    count = sum(1 for p in participants.values() if p["event_id"] == ev["id"])
    if count >= ev["max_participants"]:
        raise HTTPException(status_code=400, detail="EVENT FULL")
    # duplicate prevention: check same name+team in event (simple heuristic)
    # Don't block refresh: if same name+team exists, return existing session instead of duplicate?
    # For MVP: allow but check session reuse via client; here just create new but warn if duplicate name
    # We implement idempotent: if exact name+team exists, return that participant (prevent accidental double)
    name_norm = payload.name.strip()
    if not name_norm:
        raise HTTPException(status_code=400, detail="Name required")
    for p in participants.values():
        if p["event_id"] == ev["id"] and p["name"].lower() == name_norm.lower() and p["team_id"] == payload.team_id:
            # return existing instead of creating duplicate
            return ParticipantOut(
                id=p["id"],
                session_id=p["session_id"],
                name=p["name"],
                team_id=p["team_id"],
                team_name=teams[p["team_id"]]["name"],
                event_id=ev["id"]
            )
    pid = "p_" + uuid.uuid4().hex[:8]
    sid = "sess_" + uuid.uuid4().hex[:12]
    p = {
        "id": pid,
        "session_id": sid,
        "name": name_norm,
        "team_id": payload.team_id,
        "event_id": ev["id"],
        "event_code": ev["code"],
    }
    participants[pid] = p
    _save_parts(participants)
    return ParticipantOut(
        id=pid,
        session_id=sid,
        name=name_norm,
        team_id=payload.team_id,
        team_name=teams[payload.team_id]["name"],
        event_id=ev["id"]
    )

@router.get("/api/events/{event_id}/participants", response_model=list[ParticipantOut])
def list_participants(event_id: str):
    events = _events()
    ev = None
    for e in events.values():
        if e["id"] == event_id or e["code"] == event_id:
            event_id = e["id"]
            ev = e
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    participants = _participants()
    teams = _teams()
    out = []
    for p in participants.values():
        if p["event_id"] == event_id:
            team_name = teams.get(p["team_id"], {}).get("name", "Unknown")
            out.append({
                "id": p["id"],
                "session_id": p["session_id"],
                "name": p["name"],
                "team_id": p["team_id"],
                "team_name": team_name,
                "event_id": p["event_id"]
            })
    return out
