from fastapi import APIRouter, HTTPException
import uuid
from models.schemas import TeamCreate, TeamUpdate, TeamOut
from storage import json_store

router = APIRouter(tags=["teams"])

def _teams():
    return json_store.load("teams", {})

def _participants():
    return json_store.load("participants", {})

def _events():
    return json_store.load("events", {})

def _save_teams(d):
    json_store.save("teams", d)

@router.post("/api/events/{event_id}/teams", response_model=TeamOut)
def create_team(event_id: str, payload: TeamCreate):
    events = _events()
    ev = None
    for e in events.values():
        if e["id"] == event_id or e["code"] == event_id:
            ev = e
            event_id = e["id"]
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    teams = _teams()
    event_teams = [t for t in teams.values() if t["event_id"] == event_id]
    if len(event_teams) >= 24:
        raise HTTPException(status_code=400, detail="Each event can have at most 24 teams")
    used_names = {t["name"] for t in event_teams}
    name = next(
        (f"TEAM_{index:02d}" for index in range(1, 25) if f"TEAM_{index:02d}" not in used_names),
        None,
    )
    if name is None:
        raise HTTPException(status_code=400, detail="No team name available")
    tid = "team_" + uuid.uuid4().hex[:6]
    team = {"id": tid, "event_id": event_id, "name": name}
    teams[tid] = team
    _save_teams(teams)
    return {**team, "member_count": 0}

@router.get("/api/events/{event_id}/teams", response_model=list[TeamOut])
def list_teams(event_id: str):
    events = _events()
    ev = None
    for e in events.values():
        if e["id"] == event_id or e["code"] == event_id:
            event_id = e["id"]
            ev = e
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    teams = _teams()
    participants = _participants()
    out = []
    for t in teams.values():
        if t["event_id"] == event_id:
            cnt = sum(1 for p in participants.values() if p.get("team_id") == t["id"])
            out.append({"id": t["id"], "event_id": t["event_id"], "name": t["name"], "member_count": cnt})
    return out

@router.put("/api/teams/{team_id}", response_model=TeamOut)
def update_team(team_id: str, payload: TeamUpdate):
    raise HTTPException(status_code=400, detail="Team names are fixed")

@router.delete("/api/teams/{team_id}")
def delete_team(team_id: str):
    teams = _teams()
    if team_id not in teams:
        raise HTTPException(status_code=404, detail="Team not found")
    participants = _participants()
    # prevent delete if members exist
    if any(p.get("team_id") == team_id for p in participants.values()):
        raise HTTPException(status_code=400, detail="Cannot delete team with members")
    del teams[team_id]
    _save_teams(teams)
    return {"ok": True}
