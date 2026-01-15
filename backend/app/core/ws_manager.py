from typing import Dict, Set
from uuid import UUID
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class WSRoomManager:
    def __init__(self):
        self._conns: Dict[UUID, Set[WebSocket]] = {}

    async def connect(self, room_id: UUID, ws: WebSocket):
        await ws.accept()
        self._conns.setdefault(room_id, set()).add(ws)

    def disconnect(self, room_id: UUID, ws: WebSocket):
        if room_id in self._conns:
            self._conns[room_id].discard(ws)
            if not self._conns[room_id]:
                self._conns.pop(room_id, None)

    async def broadcast(self, room_id: UUID, payload: dict):
        conns = list(self._conns.get(room_id, set()))
        logger.info(
            f"[WS:BROADCAST] room={room_id} "
            f"connections={len(conns)} "
        )
        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(room_id, ws)

room_ws_manager = WSRoomManager()
graph_ws_manager = WSRoomManager()