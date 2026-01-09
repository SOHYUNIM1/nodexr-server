from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.utterances.utterances_req import UtterancesReq
from app.schemas.graph.graph_resp import GraphResp
from app.services.utterance_queue import enqueue_utterance

router = APIRouter()

@router.post("", response_model=GraphResp)
async def post_utterance(req: UtterancesReq, db: Session = Depends(get_db)):
    # db는 여기서 안 쓰지만 DI 유지 (추후 확장용)
    return await enqueue_utterance(req)
