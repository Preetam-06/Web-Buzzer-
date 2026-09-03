from typing import Dict, Set
from fastapi import WebSocket
import json

class ConnectionManager:
    def __init__(self):
        # event_code -> set of websockets
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, event_code: str):
        await ws.accept()
        if event_code not in self.rooms:
            self.rooms[event_code] = set()
        self.rooms[event_code].add(ws)

    def disconnect(self, ws: WebSocket, event_code: str):
        if event_code in self.rooms:
            self.rooms[event_code].discard(ws)
            if not self.rooms[event_code]:
                del self.rooms[event_code]

    async def broadcast(self, event_code: str, message: dict):
        if event_code not in self.rooms:
            return
        dead = []
        data = json.dumps(message)
        for ws in list(self.rooms[event_code]):
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, event_code)

manager = ConnectionManager()
