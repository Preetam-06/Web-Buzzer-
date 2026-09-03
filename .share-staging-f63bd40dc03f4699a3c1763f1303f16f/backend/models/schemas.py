from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class EventStatus(str, Enum):
    CREATED = "CREATED"
    REGISTRATION_OPEN = "REGISTRATION_OPEN"
    READY = "READY"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"

class RoundStatus(str, Enum):
    WAITING = "WAITING"
    QUESTION_ACTIVE = "QUESTION_ACTIVE"
    BUZZER_OPEN = "BUZZER_OPEN"
    BUZZER_LOCKED = "BUZZER_LOCKED"
    ANSWERING = "ANSWERING"
    COMPLETED = "COMPLETED"

class EventCreate(BaseModel):
    name: str
    code: str = Field(pattern=r"^[A-Za-z0-9_-]{3,20}$")
    max_participants: int = 50

class EventUpdate(BaseModel):
    name: Optional[str] = None
    max_participants: Optional[int] = None
    status: Optional[EventStatus] = None

class EventOut(BaseModel):
    id: str
    name: str
    code: str
    max_participants: int
    status: EventStatus
    current_round_id: Optional[str] = None
    current_question_id: Optional[str] = None

class TeamCreate(BaseModel):
    name: str

class TeamUpdate(BaseModel):
    name: str

class TeamOut(BaseModel):
    id: str
    event_id: str
    name: str
    score: int = 0
    member_count: int = 0

class ParticipantJoin(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    team_id: str

class ParticipantOut(BaseModel):
    id: str
    session_id: str
    name: str
    team_id: str
    team_name: str
    event_id: str

class QuestionCreate(BaseModel):
    text: str
    number: Optional[int] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    image: Optional[str] = None

class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    number: Optional[int] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    image: Optional[str] = None

class QuestionOut(BaseModel):
    id: str
    event_id: str
    number: int
    text: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    image: Optional[str] = None

class BuzzerRequest(BaseModel):
    participant_id: str
    session_id: str
    round_id: str

class ScoreCorrectRequest(BaseModel):
    points: int = 10

class LeaderboardEntry(BaseModel):
    team_id: str
    team_name: str
    score: int
    rank: int

class BuzzWinner(BaseModel):
    participant_id: str
    participant_name: str
    team_id: str
    team_name: str
    timestamp: str
