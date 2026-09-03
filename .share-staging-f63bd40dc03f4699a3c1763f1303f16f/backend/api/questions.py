from fastapi import APIRouter, HTTPException
import uuid
from models.schemas import QuestionCreate, QuestionUpdate, QuestionOut
from storage import json_store

router = APIRouter(tags=["questions"])

def _questions():
    return json_store.load("questions", {})
def _events():
    return json_store.load("events", {})

@router.post("/api/events/{event_id}/questions", response_model=QuestionOut)
def create_question(event_id: str, payload: QuestionCreate):
    events = _events()
    ev = None
    for e in events.values():
        if e["id"] == event_id or e["code"] == event_id:
            ev = e
            event_id = e["id"]
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    questions = _questions()
    # auto number
    existing_nums = [q["number"] for q in questions.values() if q["event_id"] == event_id]
    num = payload.number if payload.number is not None else (max(existing_nums) + 1 if existing_nums else 1)
    qid = "q_" + uuid.uuid4().hex[:8]
    q = {
        "id": qid,
        "event_id": event_id,
        "number": num,
        "text": payload.text.strip(),
        "options": payload.options,
        "correct_answer": payload.correct_answer,
        "image": payload.image,
    }
    if not q["text"]:
        raise HTTPException(status_code=400, detail="Question text required")
    questions[qid] = q
    json_store.save("questions", questions)
    return q

@router.get("/api/events/{event_id}/questions", response_model=list[QuestionOut])
def list_questions(event_id: str):
    events = _events()
    for e in events.values():
        if e["id"] == event_id or e["code"] == event_id:
            event_id = e["id"]
            break
    else:
        raise HTTPException(status_code=404, detail="Event not found")
    questions = _questions()
    lst = [q for q in questions.values() if q["event_id"] == event_id]
    lst.sort(key=lambda x: x["number"])
    return lst

@router.put("/api/questions/{question_id}", response_model=QuestionOut)
def update_question(question_id: str, payload: QuestionUpdate):
    questions = _questions()
    if question_id not in questions:
        raise HTTPException(status_code=404, detail="Question not found")
    q = questions[question_id]
    if payload.text is not None:
        q["text"] = payload.text.strip()
    if payload.number is not None:
        q["number"] = payload.number
    if payload.options is not None:
        q["options"] = payload.options
    if payload.correct_answer is not None:
        q["correct_answer"] = payload.correct_answer
    if payload.image is not None:
        q["image"] = payload.image
    questions[question_id] = q
    json_store.save("questions", questions)
    return q

@router.delete("/api/questions/{question_id}")
def delete_question(question_id: str):
    questions = _questions()
    if question_id not in questions:
        raise HTTPException(status_code=404, detail="Question not found")
    del questions[question_id]
    json_store.save("questions", questions)
    return {"ok": True}

# reorder endpoint
from pydantic import BaseModel
class ReorderReq(BaseModel):
    order: list[str]  # list of question ids in desired order

@router.post("/api/events/{event_id}/questions/reorder")
def reorder(event_id: str, payload: ReorderReq):
    events = _events()
    for e in events.values():
        if e["id"] == event_id or e["code"] == event_id:
            event_id = e["id"]
            break
    else:
        raise HTTPException(status_code=404, detail="Event not found")
    questions = _questions()
    for idx, qid in enumerate(payload.order, start=1):
        if qid in questions and questions[qid]["event_id"] == event_id:
            questions[qid]["number"] = idx
    json_store.save("questions", questions)
    return {"ok": True}
