from typing import List, Dict, Any
from fastapi import WebSocket
import json
import asyncio


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(ws)

    def disconnect(self, session_id: str, ws: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(ws)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def push(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            for ws in self.active_connections[session_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    pass

    async def push_step(self, session_id: str, step: int, status: str, message: str = ""):
        await self.push(session_id, {
            "type": "step_update",
            "step": step,
            "status": status,
            "message": message,
        })

    async def push_log(self, session_id: str, step: str, status: str, log: str):
        await self.push(session_id, {
            "type": "log",
            "step": step,
            "status": status,
            "log": log,
        })


ws_manager = ConnectionManager()
