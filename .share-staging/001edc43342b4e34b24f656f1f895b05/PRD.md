# Faculty Trivia Buzzer — Product Requirements Document

## 1. Product Overview

Faculty Trivia Buzzer is a real-time web application for team-based trivia competitions.

Participants join an event from their mobile phones using a QR code. Each participant belongs to a team and receives a large digital BUZZ button.

Questions are displayed on a projector through a dedicated Vue.js display page.

When the host opens the buzzer, participants compete to press the button first.

The backend determines the first valid participant to buzz and immediately displays:

- Contestant name
- Team name

The winning team receives the opportunity to answer verbally.

The application does NOT require participants to submit answers through their phones.

---

# 2. Primary Goal

Provide a simple, fast and reliable digital buzzer system for live team-based trivia events.

The system must prioritize:

1. Low latency
2. Reliable first-buzzer detection
3. Simple participant experience
4. Simple host controls
5. Clear projector display
6. Team-based scoring
7. Easy local deployment

---

# 3. Target Users

## 3.1 Host / Admin

Controls the event.

Responsibilities:

- Create event
- Create teams
- Manage participants
- Add questions
- Start questions
- Open buzzer
- Reset buzzer
- Judge answers
- Award points
- View leaderboard
- End event

## 3.2 Contestant

Uses a mobile browser.

Responsibilities:

- Scan QR
- Enter name
- Select team
- Join event
- Wait for buzzer
- Press BUZZ

## 3.3 Display

A read-only Vue.js interface running on the projector computer.

Responsibilities:

- Display event
- Display question
- Display buzzer status
- Display first contestant
- Display team name
- Display scores
- Display leaderboard

---

# 4. Core User Flow

## Participant Flow

QR Code
→ Join Page
→ Enter Name
→ Select Team
→ Join
→ Waiting Screen
→ Buzzer Opens
→ Press BUZZ
→ Result

---

## Host Flow

Admin Login
→ Create Event
→ Create Teams
→ Add Questions
→ Generate QR
→ Participants Join
→ Start Question
→ Open Buzzer
→ Winner Selected
→ Judge Answer
→ Award Points
→ Reset
→ Next Question

---

## Display Flow

Waiting
→ Question
→ Buzzer Open
→ First Buzzer
→ Winner
→ Score Update
→ Next Question

---

# 5. Functional Requirements

## FR-001 Event Creation

Admin shall be able to create an event.

Event fields:

- Event name
- Event code
- Participant limit
- Status

Default participant limit:

50

The participant limit must be configurable by Admin.

---

# 6. Team Management

Admin shall be able to:

- Create teams
- Rename teams
- Delete teams
- View team members
- View team score

Example:

Team A
Team B
Team C
Team D

Participants select an existing team during registration.

---

# 7. Participant Registration

Participants join through a QR code.

The QR code contains the event join URL.

Participant enters:

- Name
- Team

The backend validates the request.

If capacity is available, participant is registered.

---

# 8. Participant Capacity

Default:

50 participants.

Admin can change the limit.

Example:

50
75
100
150

The backend must enforce the limit.

The frontend must never be trusted to enforce capacity.

If the limit is reached:

EVENT FULL

New participants cannot join.

---

# 9. Duplicate Registration

The system should prevent accidental duplicate registrations.

Each participant receives a session ID.

Refreshing the browser should not automatically create another participant.

---

# 10. Question Management

Admin shall be able to:

- Add questions
- Edit questions
- Delete questions
- Reorder questions
- Select current question

Question fields:

- Question ID
- Question number
- Question text
- Optional image
- Optional options
- Optional correct answer

Questions are displayed on the projector.

---

# 11. Question Display

The question is displayed through the Vue.js `/display` page.

The display is designed like a PowerPoint slide.

Requirements:

- 16:9 layout
- Large text
- High contrast
- Full-screen capable
- Responsive
- Projector-friendly
- Minimal controls

No PowerPoint file is required.

---

# 12. Buzzer

Each participant receives one large BUZZ button.

The button is enabled only when the Admin opens the buzzer.

States:

- Waiting
- Ready
- Buzzer Open
- Buzzer Closed
- Winner
- Disconnected

---

# 13. First Buzzer Detection

When the buzzer is open, multiple participants may press simultaneously.

The backend must determine exactly one winner for the round.

The winner consists of:

- Participant ID
- Participant name
- Team ID
- Team name
- Timestamp

The first successful atomic Redis claim becomes the winner.

---

# 14. Winner Display

After a winner is selected, the projector immediately shows:

FIRST BUZZER

Contestant:
Preetam

Team:
Team A

The winner's team receives the opportunity to answer.

All other participants see:

BUZZER CLOSED

---

# 15. Buzzer Lock

After the first valid buzzer:

- Buzzer automatically closes
- Further buzz requests are rejected
- Winner cannot be replaced
- Display changes to winner state

---

# 16. Answer Evaluation

The participant answers verbally.

The Admin determines whether the answer is correct.

Admin controls:

[ CORRECT ]

[ WRONG ]

No participant answer submission is required.

---

# 17. Scoring

Admin can award points to the winning team.

Example:

Correct answer:

Team A +10

Incorrect answer:

Team A +0

The scoring value should be configurable by Admin if required.

---

# 18. Leaderboard

The system displays team scores.

Example:

1. Team A — 80
2. Team C — 60
3. Team B — 50
4. Team D — 30

Individual buzzer statistics may also be shown.

Example:

Top Buzzer Contestants

1. Preetam — Team A — 5 buzzer wins
2. Rahul — Team B — 3 buzzer wins

---

# 19. Round Management

Each question represents one round.

Round states:

WAITING
QUESTION_ACTIVE
BUZZER_OPEN
BUZZER_LOCKED
ANSWERING
COMPLETED

Admin can:

- Start round
- Open buzzer
- Reset round
- Mark answer correct
- Mark answer wrong
- Move to next question

---

# 20. Admin Dashboard

Dashboard must display:

- Event name
- Participant count
- Maximum participants
- Teams
- Current question
- Current round
- Buzzer state
- Current winner
- Team scores

Main controls:

START QUESTION
OPEN BUZZER
RESET BUZZER
CORRECT
WRONG
NEXT QUESTION
END EVENT

---

# 21. QR Code

Admin can generate a QR code for the event.

QR destination:

/join/{event_code}

The QR can be displayed on the projector or printed.

---

# 22. Real-Time Communication

WebSockets shall be used for real-time updates.

Events include:

QUESTION_STARTED
BUZZER_OPEN
BUZZER_WINNER
BUZZER_CLOSED
ROUND_RESET
SCORE_UPDATED
LEADERBOARD_UPDATED
EVENT_ENDED

---

# 23. Data Persistence

Initial implementation uses JSON.

Data:

- Events
- Teams
- Participants
- Questions
- Scores
- Results

Redis is NOT the permanent database.

Redis is used for temporary real-time state.

---

# 24. Performance Requirements

The buzzer path must be minimal.

Critical path:

Mobile
→ WebSocket
→ FastAPI
→ Redis atomic operation
→ Winner
→ WebSocket broadcast
→ Display

The system must NOT:

- Write JSON before determining winner
- Query a slow persistent database before determining winner
- Use polling for buzzer state
- Let the browser decide the winner

---

# 25. Network Requirements

The preferred event deployment is a private local network.

Internet is not required for the core application.

All devices connect to the same local network:

- Participant phones
- Server
- Admin device
- Projector device

The server can run locally.

---

# 26. Security Requirements

Admin functionality requires authentication.

Participant sessions require validation.

Backend must validate:

- Event ID
- Participant session
- Team
- Round
- Buzzer state

The client cannot declare itself the winner.

---

# 27. Error Handling

The system must handle:

- Event full
- Invalid event
- Invalid session
- Duplicate join
- Buzzer closed
- Buzzer already won
- WebSocket disconnect
- Server restart
- Display reconnect
- Admin reconnect

---

# 28. MVP Scope

The MVP includes:

- Admin login
- Event creation
- Team creation
- Participant registration
- QR code
- Participant limit
- Question management
- Projector display
- Mobile buzzer
- WebSocket
- Redis
- First-winner lock
- Winner display
- Team scoring
- Leaderboard
- JSON persistence
- Reset and next question

---

# 29. Out of Scope

Not required for MVP:

- Native Android app
- Native iOS app
- Participant accounts
- Payment
- AI-generated questions
- Cloud infrastructure
- PostgreSQL
- Microservices
- Kubernetes
- Advanced analytics
- Automatic answer evaluation
- Hardware buzzers

---

# 30. Success Criteria

The product is successful when:

1. Admin can create an event.
2. Admin can create teams.
3. QR code allows participants to join.
4. Participant can enter name and team.
5. System enforces participant limit.
6. Admin can change participant limit.
7. Admin can create questions.
8. Projector displays questions.
9. Admin can open the buzzer.
10. Participants can press BUZZ.
11. Redis selects one winner.
12. Winner's name appears on projector.
13. Winner's team appears on projector.
14. Other participants are locked.
15. Admin can award points.
16. Team score updates immediately.
17. Admin can reset the round.
18. Admin can move to the next question.
19. Final leaderboard is displayed.
20. Results survive application restart through JSON persistence.