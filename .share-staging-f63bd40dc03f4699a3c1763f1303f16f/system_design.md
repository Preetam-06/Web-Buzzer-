# Faculty Trivia Buzzer — System Design

## 1. System Overview

Faculty Trivia Buzzer is a local-first real-time web application designed for team-based trivia competitions.

The system consists of:

1. Admin Panel
2. Participant Mobile Interface
3. Projector Display
4. FastAPI Backend
5. WebSocket Communication
6. Redis Real-Time State
7. JSON Persistent Storage

The application is intentionally designed as a modular monolith.

There is no need for microservices in the MVP.


# 2. High-Level Architecture


                    ┌─────────────────────┐
                    │      ADMIN          │
                    │    Vue + Vite       │
                    └──────────┬──────────┘
                               │
                         HTTP / WebSocket
                               │
                               ▼
                    ┌─────────────────────┐
                    │       FastAPI       │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
              ┌───────────┐        ┌────────────┐
              │   Redis   │        │ JSON Store │
              │           │        │            │
              │ Live State│        │ Questions  │
              │ Buzzer    │        │ Teams      │
              │ Winner    │        │ Scores     │
              │ Round     │        │ Results    │
              └─────┬─────┘        └────────────┘
                    │
                WebSocket
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
   ┌──────────────┐    ┌───────────────┐
   │ Participant  │    │   Projector   │
   │ Mobile Vue   │    │  Vue Display  │
   └──────────────┘    └───────────────┘


# 3. Architecture Style

The MVP uses a modular monolith.

FastAPI contains:

- API routes
- WebSocket manager
- Event logic
- Team logic
- Participant logic
- Question logic
- Buzzer logic
- Score logic

This avoids unnecessary infrastructure while keeping the code organized.


# 4. Frontend Architecture

Frontend:

Vue 3
+
Vite

Three primary interfaces:

/admin
/join/{event_code}
/play
/display/{event_code}


## Admin

Responsibilities:

- Event configuration
- Team management
- Question management
- Round control
- Score management
- Results


## Participant

Responsibilities:

- Registration
- Team selection
- Buzzer
- Status


## Display

Responsibilities:

- Question presentation
- Buzzer state
- Winner presentation
- Scores
- Leaderboard


# 5. Frontend Components

Suggested structure:

frontend/

src/

├── components/
│   ├── BuzzerButton.vue
│   ├── TeamCard.vue
│   ├── QuestionCard.vue
│   ├── WinnerCard.vue
│   ├── ScoreBoard.vue
│   ├── ParticipantCount.vue
│   └── QRCode.vue
│
├── views/
│   ├── AdminView.vue
│   ├── JoinView.vue
│   ├── PlayView.vue
│   └── DisplayView.vue
│
├── services/
│   ├── api.js
│   └── websocket.js
│
├── router/
│   └── index.js
│
├── stores/
│   └── game.js
│
├── App.vue
└── main.js


# 6. Backend Architecture

Suggested structure:

backend/

├── main.py
│
├── api/
│   ├── auth.py
│   ├── events.py
│   ├── teams.py
│   ├── participants.py
│   ├── questions.py
│   ├── rounds.py
│   └── scores.py
│
├── websocket/
│   ├── manager.py
│   └── events.py
│
├── services/
│   ├── event_service.py
│   ├── team_service.py
│   ├── participant_service.py
│   ├── question_service.py
│   ├── buzzer_service.py
│   └── score_service.py
│
├── storage/
│   ├── json_store.py
│   └── files.py
│
├── redis/
│   ├── client.py
│   └── buzzer.py
│
├── models/
│   └── schemas.py
│
└── config/
    └── settings.py


# 7. Event Lifecycle

An event has a lifecycle:

CREATED
   ↓
REGISTRATION_OPEN
   ↓
READY
   ↓
RUNNING
   ↓
FINISHED


# 8. Round Lifecycle

Each question is a round.

WAITING
   ↓
QUESTION_ACTIVE
   ↓
BUZZER_OPEN
   ↓
BUZZER_LOCKED
   ↓
ANSWERING
   ↓
COMPLETED
   ↓
NEXT ROUND


# 9. Participant Registration Flow

Participant scans QR.

Example:

/join/FACULTY26

Frontend sends:

POST /api/events/FACULTY26/join

Payload:

{
  "name": "Preetam",
  "team_id": "team_a"
}

Backend:

1. Validate event
2. Check event status
3. Check capacity
4. Validate team
5. Create participant
6. Create session
7. Return participant session

Response:

{
  "participant_id": "p123",
  "session_id": "session_xyz",
  "team_id": "team_a"
}


# 10. Capacity Control

Capacity is stored in event configuration.

Example:

{
  "max_participants": 50
}

The backend checks:

current_count < max_participants

before registration.

The frontend count is informational only.


# 11. Question Architecture

Questions are stored in JSON.

Example:

{
  "id": "q001",
  "event_id": "event001",
  "number": 1,
  "text": "Which planet is known as the Red Planet?",
  "options": [
    "Earth",
    "Mars",
    "Jupiter",
    "Venus"
  ],
  "correct_answer": "Mars"
}


# 12. Buzzer Architecture

The buzzer is the critical system component.

When the Admin opens the buzzer:

Redis state becomes:

round:123:status = OPEN

Participant presses BUZZ.

Request:

{
  "type": "BUZZ",
  "round_id": "123",
  "participant_id": "p123"
}


# 13. Buzzer Validation

FastAPI validates:

1. Participant exists
2. Participant session is valid
3. Event exists
4. Round exists
5. Round is active
6. Buzzer is open


# 14. Atomic Winner Selection

Do NOT use:

if winner is None:
    winner = participant

This is unsafe under concurrent requests.

Instead use an atomic Redis operation.

Conceptually:

SET round:123:winner p123 NX

NX means:

Set the value only if the key does not already exist.

First successful request wins.

All subsequent requests fail.


# 15. Buzzer Critical Path

The critical path is:

Participant
   ↓
WebSocket
   ↓
FastAPI
   ↓
Validation
   ↓
Redis atomic SET NX
   ↓
Winner
   ↓
Redis buzzer CLOSED
   ↓
WebSocket broadcast
   ↓
All clients update


# 16. Important Performance Rule

Persistent storage MUST NOT be in the critical winner-selection path.

Bad:

Phone
→ FastAPI
→ JSON write
→ database
→ determine winner

Preferred:

Phone
→ FastAPI
→ Redis
→ determine winner
→ broadcast
→ persist result


# 17. Result Persistence

After winner selection, the backend stores:

{
  "round_id": "123",
  "question_id": "q007",
  "participant_id": "p123",
  "participant_name": "Preetam",
  "team_id": "team_a",
  "team_name": "Team A",
  "timestamp": "...",
  "points": 10
}

This is written to results.json.


# 18. WebSocket Architecture

Each client connects to:

/ws/event/{event_code}

The server maintains connections by event.

Example:

event FACULTY26

Connections:

- Admin
- Display
- Participant 1
- Participant 2
- ...
- Participant 50


# 19. WebSocket Events

## QUESTION_STARTED

{
  "type": "QUESTION_STARTED",
  "question_id": "q007",
  "number": 7,
  "text": "..."
}


## BUZZER_OPEN

{
  "type": "BUZZER_OPEN",
  "round_id": "r007"
}


## BUZZER_WINNER

{
  "type": "BUZZER_WINNER",
  "participant": {
    "id": "p123",
    "name": "Preetam"
  },
  "team": {
    "id": "team_a",
    "name": "Team A"
  }
}


## BUZZER_CLOSED

{
  "type": "BUZZER_CLOSED"
}


## SCORE_UPDATED

{
  "type": "SCORE_UPDATED",
  "team_id": "team_a",
  "score": 40
}


# 20. Display Architecture

The projector connects to:

/display/FACULTY26

The display is read-only.

It receives WebSocket events.

Display states:

WELCOME
WAITING
QUESTION
BUZZER_OPEN
WINNER
ANSWER_RESULT
LEADERBOARD
FINISHED


# 21. Display Design

Target:

16:9

The UI should resemble a modern presentation slide.

Design principles:

- Large typography
- Minimal controls
- High contrast
- Large winner name
- Large team name
- Clear question
- Full-screen support
- Smooth transitions


# 22. Participant UI

Mobile-first.

Primary screen:

TEAM A

PREETAM

[ BUZZ ]

The button must be:

- Large
- Touch friendly
- Easy to locate
- Fast to respond
- Disabled when buzzer is closed


# 23. Admin Architecture

Admin controls the game state.

Admin actions:

CREATE_EVENT
CREATE_TEAM
ADD_QUESTION
START_QUESTION
OPEN_BUZZER
RESET_BUZZER
MARK_CORRECT
MARK_WRONG
NEXT_QUESTION
END_EVENT


# 24. API Endpoints

## Authentication

POST /api/auth/login


## Events

POST /api/events

GET /api/events/{event_id}

PUT /api/events/{event_id}


## Participants

POST /api/events/{event_code}/join

GET /api/events/{event_id}/participants


## Teams

POST /api/events/{event_id}/teams

GET /api/events/{event_id}/teams

PUT /api/teams/{team_id}

DELETE /api/teams/{team_id}


## Questions

POST /api/events/{event_id}/questions

GET /api/events/{event_id}/questions

PUT /api/questions/{question_id}

DELETE /api/questions/{question_id}


## Round Control

POST /api/events/{event_id}/round/start

POST /api/events/{event_id}/round/open-buzzer

POST /api/events/{event_id}/round/reset

POST /api/events/{event_id}/round/next


## Scoring

POST /api/events/{event_id}/score/correct

POST /api/events/{event_id}/score/wrong

GET /api/events/{event_id}/leaderboard


## WebSocket

WS /ws/event/{event_code}


# 25. JSON Storage

Directory:

data/

├── events.json
├── teams.json
├── participants.json
├── questions.json
└── results.json


# 26. Redis Data

Redis contains temporary event state.

Example:

event:FACULTY26:current_round

event:FACULTY26:buzzer_status

round:r007:winner

round:r007:status


# 27. Redis Expiration

Temporary round keys should have a TTL where appropriate.

This prevents stale state from surviving indefinitely after an abnormal shutdown.

Example:

round:r007:winner
TTL: event-defined duration


# 28. Concurrency

The most important concurrency scenario is:

Participant A
Participant B
Participant C

all press at approximately the same time.

Every request reaches the backend.

Redis atomic operation:

SET winner NX

Only one request succeeds.

That participant becomes the official winner.


# 29. Reconnection

WebSocket clients may disconnect.

When a client reconnects:

1. Establish WebSocket
2. Authenticate/session validate
3. Request current event state
4. Receive current round
5. Receive buzzer state
6. Update UI

The client should not assume its previous state is still valid.


# 30. Failure Handling

## Redis unavailable

The buzzer should be disabled.

Do NOT fall back to unsafe in-memory winner selection unless explicitly designed and tested.

Display:

REAL-TIME SERVICE UNAVAILABLE


## JSON storage failure

The live buzzer can continue temporarily because Redis handles live state.

The system should report persistence failure to Admin.

## Display disconnect

Display reconnects automatically.

## Participant disconnect

Participant can reconnect using session information.


# 31. Security Model

Admin:

Authenticated.

Participant:

Session-based.

Buzzer request must include:

- Session ID
- Participant ID
- Round ID


The backend verifies all three.

A participant cannot send:

{
  "participant_id": "someone_else"
}

and claim another participant's identity.


# 32. Rate Limiting

Buzzer requests should be rate limited.

A participant repeatedly sending BUZZ requests should not overload the server.

Example policy:

Allow only a small number of buzzer requests per second per session.

Normal users will send one request per round.


# 33. Network Architecture

Preferred event network:

             PRIVATE WI-FI
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
      Phones     Server     Display
      1–50       Laptop      Laptop

Internet is optional.

The server should have a stable local IP address.


# 34. Local Deployment

Server machine runs:

FastAPI
Redis
Frontend

Example:

http://192.168.1.10


Participant:

http://192.168.1.10/join/FACULTY26


Admin:

http://192.168.1.10/admin


Display:

http://192.168.1.10/display/FACULTY26


# 35. Docker

Optional for MVP.

Recommended services:

services:

  backend:
    FastAPI

  redis:
    Redis

  frontend:
    Vue/Vite build served through a web server


Docker makes event setup reproducible.


# 36. Why Not PostgreSQL Initially?

The expected event size is small.

Initial requirement:

~50 participants

JSON is sufficient for:

- Teams
- Participants
- Questions
- Scores
- Results

PostgreSQL would add:

- Database setup
- Connection management
- Migrations
- Backup configuration

without solving the critical buzzer problem.

Redis already handles the real-time race.

PostgreSQL can be introduced later without redesigning the buzzer protocol.


# 37. Why Redis?

Redis provides:

- Very fast memory operations
- Atomic commands
- TTL
- Simple state management
- Reliable concurrency primitives

The most important operation is:

SET key value NX

This allows one participant to claim the current round.


# 38. Latency Strategy

The application cannot guarantee zero latency.

It can minimize application-induced latency.

Strategies:

1. Local network
2. WebSockets
3. Redis atomic operation
4. Minimal buzzer payload
5. No database query in winner path
6. No JSON write in winner path
7. Lightweight Vue participant page
8. Persistent WebSocket connection
9. Automatic reconnect
10. Stable local server


# 39. State Ownership

Vue:

Displays state.

FastAPI:

Controls business rules.

Redis:

Controls live round state and winner lock.

JSON:

Stores persistent event data.


# 40. Final Architecture

Frontend:

Vue 3
+
Vite

Backend:

FastAPI

Real-time:

WebSocket

Live state:

Redis

Persistence:

JSON

Network:

Private local Wi-Fi

Deployment:

Single local server

Participants:

Maximum 50 initially

Admin:

Can increase capacity


# 41. Core Principle

The application should remain a small modular monolith.

Do not add:

PostgreSQL
Microservices
Cloud infrastructure
Kubernetes
Native mobile applications

until actual requirements justify them.

The critical feature is not the number of technologies.

The critical feature is:

FASTAPI
→ REDIS ATOMIC WINNER LOCK
→ WEBSOCKET BROADCAST
→ INSTANT DISPLAY UPDATE


# 42. Future Migration

If the event grows from:

50 → 500 → 5,000 participants

the persistence layer can move:

JSON
→ PostgreSQL

The real-time layer can remain:

WebSocket
+
Redis

The frontend does not need to change fundamentally.