import asyncio
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db import models
from app.services.llm_service import LLMService
from app.services.graph_build import build_graph_state
from app.services.persist_service import get_latest_snapshot, persist_graph_snapshot

_llm = LLMService()

# 단일 서버 MVP: 메모리 락
_SESSION_LOCKS: dict[str, asyncio.Lock] = {}

def _get_lock(session_id: str) -> asyncio.Lock:
    if session_id not in _SESSION_LOCKS:
        _SESSION_LOCKS[session_id] = asyncio.Lock()
    return _SESSION_LOCKS[session_id]


def save_utterance(db: Session, session_id: UUID, user_id: Optional[str], text: str, created_at):
    u = models.Utterance(
        session_id=session_id,
        user_id=user_id,
        text=text,
        created_at=created_at,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


async def generate_graph_state_for_utterance(db: Session, session_id: UUID, utterance_text: str) -> dict:
    """
    충돌 방지:
    - session_id 단위로 한 번에 하나의 그래프 생성만 허용 (asyncio.Lock)
    """
    lock = _get_lock(str(session_id))
    async with lock:
        # 최신 스냅샷 읽기
        _, prev_state = get_latest_snapshot(db, session_id)

        # LLM skeleton
        skeleton = await _llm.generate_skeleton(utterance_text, prev_state)

        # 서버 정책 적용 → 최종 graph_state
        final_state = build_graph_state(skeleton=skeleton, prev_graph_state=prev_state)
        return final_state


def persist_graph_state_sync(db: Session, session_id: UUID, graph_state: dict):
    """
    느린 경로(백그라운드)에서 호출.
    """
    try:
        persist_graph_snapshot(db, session_id, graph_state)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise