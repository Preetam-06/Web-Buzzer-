from fastapi import APIRouter, HTTPException, Header
import uuid
from models.schemas import EventCreate, EventUpdate, EventOut, EventStatus
from storage import json_store

router = APIRouter(prefix="/api/events", tags=["events"])

def _events():
    return json_store.load("events", {})

def _save(d):
    json_store.save("events", d)

@router.post("", response_model=EventOut)
def create_event(payload: EventCreate):
    events = _events()
    # check code uniqueness
    for e in events.values():
        if e["code"] == payload.code:
            raise HTTPException(status_code=409, detail="Event code already exists")
    eid = "evt_" + uuid.uuid4().hex[:8]
    ev = {
        "id": eid,
        "name": payload.name,
        "code": payload.code,
        "max_participants": payload.max_participants,
        "team_member_limit": payload.team_member_limit,
        "status": EventStatus.CREATED.value,
        "current_round_id": None,
        "current_question_id": None,
    }
    events[eid] = ev
    _save(events)
    return ev

@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str):
    events = _events()
    # allow lookup by id or code
    for e in events.values():
        if e["id"] == event_id or e["code"] == event_id:
            return e
    raise HTTPException(status_code=404, detail="Event not found")

@router.put("/{event_id}", response_model=EventOut)
def update_event(event_id: str, payload: EventUpdate):
    events = _events()
    ev = None
    key = None
    for k, v in events.items():
        if v["id"] == event_id or v["code"] == event_id:
            ev = v
            key = k
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    if payload.name is not None:
        ev["name"] = payload.name
    if payload.max_participants is not None:
        if payload.max_participants < 1:
            raise HTTPException(status_code=400, detail="Invalid limit")
        ev["max_participants"] = payload.max_participants
    if payload.team_member_limit is not None:
        ev["team_member_limit"] = payload.team_member_limit
    if payload.status is not None:
        ev["status"] = payload.status.value if hasattr(payload.status, 'value') else payload.status
    events[key] = ev
    _save(events)
    return ev

@router.get("", response_model=list[EventOut])
def list_events():
    events = _events()
    return list(events.values())
