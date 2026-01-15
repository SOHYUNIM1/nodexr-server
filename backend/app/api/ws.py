import logging
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ws_manager import room_ws_manager, graph_ws_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/room_connect/{room_id}")
async def ws_room_connect(ws: WebSocket, room_id: UUID):
    await room_ws_manager.connect(room_id, ws)
    logger.info(f"Client connected to room {room_id}")
    try:
        while True:
            # 클라에서 보낸 메시지 확인
            message = await ws.receive_text()
            logger.info(f"Message from room {room_id}: {message}")  # 수신된 메시지 로그로 남김
    except WebSocketDisconnect:
        room_ws_manager.disconnect(room_id, ws)
        logger.info(f"Client disconnected from room {room_id}")

@router.websocket("/ws/graph_event/{room_id}")
async def ws_graph_event(ws: WebSocket, room_id: UUID):
    await graph_ws_manager.connect(room_id, ws)
    logger.info(f"Client connected to graph event for room {room_id}")
    try:
        while True:
            # 클라에서 보낸 메시지 확인
            message = await ws.receive_text()
            logger.info(f"Message from room {room_id} graph event: {message}")  # 수신된 메시지 로그로 남김
    except WebSocketDisconnect:
        graph_ws_manager.disconnect(room_id, ws)
        logger.info(f"Client disconnected from graph event for room {room_id}")