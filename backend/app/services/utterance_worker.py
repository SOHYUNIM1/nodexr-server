from app.schemas.utterances.utterances_req import UtterancesReq
from app.services.graph_core import (
    save_utterance,
    generate_graph_state,
    persist_graph_state,
    project_to_unity,
)

async def process_utterance(db, req: UtterancesReq) -> dict:
    # 1) utterance 저장
    save_utterance(db, req.session_id, req.user_id, req.text, req.normalized_created_at())

    # 2) LLM + merge → 내부 graph_state
    graph_state = await generate_graph_state(db, req.session_id, req.text)

    # 3) Unity 응답 (ID 제거)
    unity_payload = project_to_unity(graph_state)

    # 4) DB 저장 (동기, 순서 보장)
    persist_graph_state(db, req.session_id, graph_state)

    return unity_payload