from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import json, time, asyncio
from config.settings import settings
from storage import json_store
from websocket.manager import manager
from redis_state.buzzer import get_round_status, try_claim_winner, set_round_status, get_winner, clear_round
from api import auth, events, teams, participants, questions, rounds, scores, qr

app = FastAPI(title="Faculty Trivia Buzzer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(teams.router)
app.include_router(participants.router)
app.include_router(questions.router)
app.include_router(rounds.router)
app.include_router(scores.router)
app.include_router(qr.router)

@app.on_event("startup")
async def startup_check():
    from redis_state.client import get_redis, is_redis_available
    r = await get_redis()
    if r:
        print("✅ Redis READY - buzzer safe for 50+ concurrent players")
    else:
        print("⚠️  Redis NOT connected - using in-memory fallback")
        print("   For 50+ players LIVE EVENT, start Redis: docker compose up -d redis  or  docker run -p 6379:6379 redis:7-alpine")

@app.get("/api/health")
async def health():
    from redis_state.client import get_redis, is_redis_available
    r = await get_redis()
    redis_ok = r is not None
    # also check flag
    status = is_redis_available()
    return {
        "status": "ok",
        "time": time.time(),
        "redis": {
            "connected": redis_ok,
            "url": settings.REDIS_URL,
            "mode": "redis" if redis_ok else "in-memory-fallback",
            "note": "READY for 50+ players" if redis_ok else "FALLBACK - OK for testing, use Redis for 50+ live event"
        }
    }

# WebSocket endpoint
@app.websocket("/ws/event/{event_code}")
async def ws_event(ws: WebSocket, event_code: str):
    # validate event exists
    events_data = json_store.load("events", {})
    ev = None
    for v in events_data.values():
        if v["code"] == event_code or v["id"] == event_code:
            ev = v
            event_code = v["code"]  # normalize
            break
    if not ev:
        await ws.close(code=1008)
        return
    await manager.connect(ws, event_code)
    try:
        # send initial state
        # get current round info
        rid = ev.get("current_round_id")
        if rid:
            status = await get_round_status(rid)
            if status is None:
                _rounds_fb = json_store.load("rounds", {})
                status = _rounds_fb.get(rid, {}).get("status")
            winner_raw = await get_winner(rid)
            winner = None
            if winner_raw:
                try:
                    winner = json.loads(winner_raw)
                except:
                    winner = winner_raw
            else:
                # fallback to JSON winner (after restart / no redis)
                _rounds_fb = json_store.load("rounds", {})
                winner = _rounds_fb.get(rid, {}).get("winner")
            await ws.send_text(json.dumps({"type": "INIT_STATE", "round_id": rid, "status": status or "WAITING", "winner": winner, "event": ev}))
        else:
            await ws.send_text(json.dumps({"type": "INIT_STATE", "event": ev, "status": "WAITING"}))
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
            except:
                continue
            mtype = msg.get("type")
            if mtype == "BUZZ":
                # Validate buzzer request
                participant_id = msg.get("participant_id")
                session_id = msg.get("session_id")
                round_id = msg.get("round_id")
                if not all([participant_id, session_id, round_id]):
                    await ws.send_text(json.dumps({"type": "BUZZ_REJECTED", "reason": "Missing fields"}))
                    continue
                # validate participant session
                parts = json_store.load("participants", {})
                p = parts.get(participant_id)
                if not p or p.get("session_id") != session_id:
                    await ws.send_text(json.dumps({"type": "BUZZ_REJECTED", "reason": "Invalid session"}))
                    continue
                # validate event matches
                if p.get("event_id") != ev["id"]:
                    await ws.send_text(json.dumps({"type": "BUZZ_REJECTED", "reason": "Event mismatch"}))
                    continue
                # refresh current rid (event may have updated round)
                _ev_now = json_store.load("events", {}).get(ev["id"]) or ev
                cur_rid = _ev_now.get("current_round_id") or rid
                if cur_rid and round_id != cur_rid:
                    # allow if round_id matches current, else reject stale
                    await ws.send_text(json.dumps({"type": "BUZZ_REJECTED", "reason": "Invalid round"}))
                    continue
                # validate buzzer open (redis first, fallback to JSON rounds store for resilience without Redis / after restart)
                status = await get_round_status(round_id)
                if status is None:
                    _rounds_fallback = json_store.load("rounds", {})
                    status = _rounds_fallback.get(round_id, {}).get("status")
                if status != "BUZZER_OPEN":
                    await ws.send_text(json.dumps({"type": "BUZZ_REJECTED", "reason": "Buzzer not open"}))
                    continue
                # Rate limiting: simple check? For MVP allow 1 per round - if already winner, reject
                teams_data = json_store.load("teams", {})
                team = teams_data.get(p["team_id"], {})
                payload = json.dumps({
                    "participant_id": p["id"],
                    "participant_name": p["name"],
                    "team_id": p["team_id"],
                    "team_name": team.get("name", "Unknown"),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })
                won = await try_claim_winner(round_id, payload)
                if won:
                    # persist winner to rounds json (outside critical path? after winner)
                    rounds_data = json_store.load("rounds", {})
                    if round_id in rounds_data:
                        rounds_data[round_id]["winner"] = json.loads(payload)
                        rounds_data[round_id]["status"] = "BUZZER_LOCKED"
                        json_store.save("rounds", rounds_data)
                    await set_round_status(round_id, "BUZZER_LOCKED")
                    winner_obj = json.loads(payload)
                    # broadcast winner
                    await manager.broadcast(event_code, {"type": "BUZZER_WINNER", "round_id": round_id, "participant": {"id": winner_obj["participant_id"], "name": winner_obj["participant_name"]}, "team": {"id": winner_obj["team_id"], "name": winner_obj["team_name"]}, "winner": winner_obj})
                    await manager.broadcast(event_code, {"type": "BUZZER_CLOSED", "round_id": round_id})
                else:
                    # someone else already won
                    winner_raw = await get_winner(round_id)
                    winner_obj = None
                    if winner_raw:
                        try:
                            winner_obj = json.loads(winner_raw)
                        except:
                            winner_obj = None
                    if not winner_obj:
                        winner_obj = json_store.load("rounds", {}).get(round_id, {}).get("winner")
                    await ws.send_text(json.dumps({"type": "BUZZ_REJECTED", "reason": "Already claimed", "winner": winner_obj}))
            elif mtype == "PING":
                await ws.send_text(json.dumps({"type": "PONG"}))
            elif mtype == "REQUEST_STATE":
                # resend state (with JSON fallback)
                ev_now2 = json_store.load("events", {}).get(ev["id"], ev)
                rid2 = ev_now2.get("current_round_id")
                status = await get_round_status(rid2) if rid2 else "WAITING"
                if status is None and rid2:
                    status = json_store.load("rounds", {}).get(rid2, {}).get("status", "WAITING")
                winner_raw = await get_winner(rid2) if rid2 else None
                winner = None
                if winner_raw:
                    try: winner = json.loads(winner_raw)
                    except: winner = None
                else:
                    if rid2:
                        winner = json_store.load("rounds", {}).get(rid2, {}).get("winner")
                await ws.send_text(json.dumps({"type": "INIT_STATE", "round_id": rid2, "status": status, "winner": winner}))
    except WebSocketDisconnect:
        manager.disconnect(ws, event_code)
    except Exception as e:
        try:
            manager.disconnect(ws, event_code)
        except:
            pass
        # log
        print("WS error", e)

# Serve frontend static if exists
import os
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

class SPAStaticFiles(StaticFiles):
    """Serve Vue's index.html for client-side routes such as /admin."""
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            filename = path.rsplit("/", 1)[-1]
            if (
                exc.status_code == 404
                and scope["method"] in ("GET", "HEAD")
                and not path.startswith(("api/", "ws/"))
                and "." not in filename
            ):
                return FileResponse(os.path.join(self.directory, "index.html"))
            raise

if os.path.exists(frontend_dist):
    app.mount("/", SPAStaticFiles(directory=frontend_dist, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
