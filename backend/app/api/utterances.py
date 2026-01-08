import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.schemas.utterance import UtteranceIn
from app.schemas.graph import GraphState
from app.services.pipeline import (
    save_utterance,
    generate_graph_state_for_utterance,
    persist_graph_state_sync,
)

router = APIRouter()

@router.post("", response_model=GraphState)
async def post_utterance(req: UtteranceIn, db: Session = Depends(get_db)):
    # 1) utterance 저장
    try:
        save_utterance(db, req.session_id, req.user_id, req.text, req.created_at)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save utterance")

    # 2) LLM 기반 graph_state 생성 (이 결과를 Unity에 보냄)
    try:
        graph_state = await generate_graph_state_for_utterance(db, req.session_id, req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate graph: {e}")

    # 3) DB 저장은 비동기(백그라운드)로 fan-out
    async def _persist_bg(state: dict):
        bg_db = SessionLocal()
        try:
            persist_graph_state_sync(bg_db, req.session_id, state)
        except Exception as e:
            # Unity에 영향 X (eventual consistency)
            print(f"[WARN] persist failed: {e}")
        finally:
            bg_db.close()

    asyncio.create_task(_persist_bg(graph_state))

    # 4) Unity에 전체 JSON 응답
    return graph_state