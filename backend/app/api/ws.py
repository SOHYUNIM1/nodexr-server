from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ws_manager import room_ws_manager, graph_ws_manager

router = APIRouter()

@router.websocket("/ws/room_connect/{room_id}")
async def ws_room_connect(ws: WebSocket, room_id: UUID):
    await room_ws_manager.connect(room_id, ws)
    try:
        while True:
            # 클라에서 ping 보내면 여기서 받기 (유지 목적)
            _ = await ws.receive_text()
    except WebSocketDisconnect:
        room_ws_manager.disconnect(room_id, ws)

@router.websocket("/ws/graph_event/{room_id}")
async def ws_graph_event(ws: WebSocket, room_id: UUID):
    await graph_ws_manager.connect(room_id, ws)
    try:
        while True:
            _ = await ws.receive_text()
    except WebSocketDisconnect:
        graph_ws_manager.disconnect(room_id, ws)