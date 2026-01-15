from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.db.session import get_db
from app.schemas.response import ApiResponse
from app.schemas.utterance import UtteranceCreate, PhaseType
from app.core.codes import UtteranceCode, UTTERANCE_MESSAGE
from app.core.ws_manager import room_ws_manager, graph_ws_manager

from app.db.models.utterance import Utterance
from app.db.models.room import Room
from app.db.models.category import Category
from app.db.models.node import Node
from app.db.models.category_detail import CategoryDetail
from app.db.models.asset import Asset
from app.db.models.edge import Edge
from app.db.models.graph_snapshot import GraphSnapshot

from app.services.llm_service import llm_service
from app.services.image_service import image_service
from app.services.graph_builder import build_graph_state
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/utterances", tags=["Utterances"])


def _set_active_category(db: Session, room_id: UUID, category_id: UUID):
    db.query(Category).filter(Category.room_id == room_id, Category.phase == "ACTIVE").update({"phase": "INACTIVE"})
    db.query(Category).filter(Category.category_id == category_id).update({"phase": "ACTIVE"})


def _get_active_category(db: Session, room_id: UUID) -> Category | None:
    return db.query(Category).filter(Category.room_id == room_id, Category.phase == "ACTIVE").first()


@router.post("", response_model=ApiResponse)
def create_utterance(req: UtteranceCreate, bg: BackgroundTasks, db: Session = Depends(get_db)):
    # 1) utterances 저장
    utt = Utterance(user_id=req.user_id, text=req.text)
    db.add(utt)
    db.commit()
    db.refresh(utt)

    # 2) phase에 따라 후처리 (LLM/이미지/그래프)
    bg.add_task(
        _process_phase_pipeline,
        req.room_id,
        req.phase,
        req.text
    )

    return ApiResponse(
        code=UtteranceCode.UTT_SAVED,
        message=UTTERANCE_MESSAGE[UtteranceCode.UTT_SAVED],
        result={"utterance_id": utt.utterance_id}
    )


async def _process_phase_pipeline(room_id: UUID, phase: PhaseType, text: str):
    logger.info(f"[PIPELINE START] _process_phase_pipeline room={room_id}, phase={phase}")
    await _async_phase_pipeline(room_id, phase, text)


async def _async_phase_pipeline(room_id: UUID, phase: PhaseType, text: str):
    """
    3) BASIC_DISCUSS / CATEGORY_DISCUSS 흐름 구현
    """
    logger.info(f"[PIPELINE START] _async_phase_pipeline room={room_id}, phase={phase}")
    from app.db.session import SessionLocal  # 순환 import 방지용
    db = SessionLocal()
    try:
        room = db.query(Room).filter(Room.room_id == room_id).first()
        if not room:
            return

        if phase == PhaseType.BASIC_DISCUSS:
            await _pipeline_basic_discuss(db, room_id, room.room_topic, text)
        else:
            await _pipeline_category_discuss(db, room_id, text)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def _pipeline_basic_discuss(db: Session, room_id: UUID, room_topic: str, text: str):
    logger.info(f"[PIPELINE START] _pipeline_basic_discuss")
    
    # 3-1) LLM: 루트 라벨 + 카테고리들 + 스케치 프롬프트
    root_label, categories, sketch_prompt = llm_service.basic_discuss(room_topic, text)

    # 3-2) categories insert: ROOT + categories(INACTIVE), 그리고 ROOT 카테고리 ACTIVE
    root_cat = Category(room_id=room_id, category_name="ROOT", phase="ACTIVE")
    db.add(root_cat)
    db.flush()

    inserted = []
    for c in categories:
        cat = Category(room_id=room_id, category_name=c, phase="INACTIVE")
        db.add(cat)
        inserted.append(cat)
    db.flush()

    # 3-3) Nodes: 루트 CATEGORY 노드 1개
    root_node = Node(room_id=room_id, node_type="CATEGORY")
    db.add(root_node)
    db.flush()

    # 3-4) category_details: ROOT 카테고리에 루트 라벨 저장
    root_detail = CategoryDetail(
        category_id=root_cat.category_id,
        node_id=root_node.node_id,
        detail_text=root_label,
        order=1
    )
    db.add(root_detail)
    db.flush()
    
    logger.info(f"DB update 완료 - nodes, categories, category_details")
    

    # 3-5) (루트 노드만 있는 graph_state) WS 전송
    state_1 = {
        "graph_snapshot_id": None,
        "nodes": [{
            "node_id": root_node.node_id,
            "node_type": "CATEGORY",
            "label": root_label,
            "order": 0
        }],
        "edges": []
    }
    await graph_ws_manager.broadcast(room_id, {
        "event": "NODE_KEYWORD_UPDATE",
        "core_img_url": None,
        "graph_state": _stringify_uuids(state_1)
    })
    logger.info(f"NODE_KEYWORD_UPDATE ws 전송")

    # 3-6) NanoBanana: 이미지 후보군 3개 생성
    urls = await image_service.generate_images(sketch_prompt, n=3)

    # 3-7~10) ASSET 노드 3개 + assets insert + edges insert
    asset_nodes = []
    for url in urls:
        n = Node(room_id=room_id, node_type="ASSET")
        db.add(n)
        db.flush()

        a = Asset(
            node_id=n.node_id,
            category_detail_id=root_detail.category_detail_id,
            img_url=url,
            type="2D_ROOT_CANDIDATE"
        )
        db.add(a)

        e = Edge(from_node_id=root_node.node_id, to_node_id=n.node_id)
        db.add(e)

        asset_nodes.append(n)

    db.flush()
    logger.info(f"DB update 완료 - nodes, edges, assets")

    # 3-11) graph_snapshot 저장 (DB에서 구성한 그래프를 snapshot으로 박제)
    graph_state = build_graph_state(db, None, room_id)
    graph_state = _stringify_uuids(graph_state)
    snap = GraphSnapshot(room_id=room_id, graph_state=graph_state)
    db.add(snap)
    db.flush()

    # snapshot_id 주입해서 다시 저장(원하면)
    graph_state2 = build_graph_state(db, snap.graph_snapshot_id, room_id)
    graph_state2 = _stringify_uuids(graph_state2)
    snap.graph_state = graph_state2
    db.flush()

    # 3-12) 최신 snapshot 기반 WS 전송
    await graph_ws_manager.broadcast(room_id, {
        "event": "NODE_IMAGE_UPDATE",
        "core_img_url": None,
        "graph_state": _stringify_uuids(graph_state2)
    })
    logger.info(f"NODE_IMAGE_UPDATE ws 전송")
    logger.info(f"graph state :{_stringify_uuids(graph_state2)}")


async def _pipeline_category_discuss(db: Session, room_id: UUID, text: str):
    logger.info(f"_pipeline_category_discuss")
    # -------------------------------------------------
    # 1. 현재 ACTIVE 카테고리 조회
    # -------------------------------------------------
    active = _get_active_category(db, room_id)
    if not active:
        return
    logger.info(f"ACTIVE 카테고리 조회")

    # -------------------------------------------------
    # 2. LLM 호출 (카테고리 발화)
    # -------------------------------------------------
    keyword, prompt = llm_service.category_discuss(
        active.category_name,
        text
    )
    logger.info(f"llm 호출 완료 - {keyword}, {prompt}")
    
    # -------------------------------------------------
    # 3. CATEGORY 노드 생성
    # -------------------------------------------------
    category_node = Node(
        room_id=room_id,
        node_type="CATEGORY"
    )
    db.add(category_node)
    db.flush()

    # -------------------------------------------------
    # 4. 전역 CATEGORY order 계산 (room 기준)
    # -------------------------------------------------
    next_order = get_next_category_order(db, room_id)

    # -------------------------------------------------
    # 5. category_details insert
    # -------------------------------------------------
    detail = CategoryDetail(
        category_id=active.category_id,
        node_id=category_node.node_id,
        detail_text=keyword,
        order=next_order
    )
    db.add(detail)
    db.flush()
    
    logger.info(f"DB update 완료 - categories, category_details")

    # -------------------------------------------------
    # 6. 노드 키워드 업데이트 WS 전송
    #    (DB 기준 full rebuild – 기존 방식 유지)
    # -------------------------------------------------
    graph_state_partial = build_graph_state(
        db=db,
        graph_snapshot_id=None,
        room_id=room_id
    )

    await graph_ws_manager.broadcast(room_id, {
        "event": "NODE_KEYWORD_UPDATE",
        "core_img_url": None,
        "graph_state": _stringify_uuids(graph_state_partial)
    })
    logger.info(f"NODE_KEYWORD_UPDATE ws 전송")

    # -------------------------------------------------
    # 7. 카테고리 이미지 생성 (의미 분리된 함수)
    # -------------------------------------------------
    logger.info(f"나노바나나 호출")
    img_urls = await image_service.generate_category_images(
        db,
        prompt=prompt,
        n=3,
        room_id=room_id
    )

    # -------------------------------------------------
    # 8. ASSET 노드 / asset / edge insert
    # -------------------------------------------------
    for url in img_urls:
        asset_node = Node(
            room_id=room_id,
            node_type="ASSET"
        )
        db.add(asset_node)
        db.flush()

        asset = Asset(
            node_id=asset_node.node_id,
            category_detail_id=detail.category_detail_id,
            img_url=url,
            type="2D_CATEGORY_CANDIDATE"
        )
        db.add(asset)

        edge = Edge(
            from_node_id=category_node.node_id,
            to_node_id=asset_node.node_id
        )
        db.add(edge)

    db.flush()

    # -------------------------------------------------
    # 9. graph_snapshot 생성 (기존 정책 유지)
    # -------------------------------------------------
    graph_state = build_graph_state(
        db=db,
        graph_snapshot_id=None,
        room_id=room_id
    )
    graph_state = _stringify_uuids(graph_state)

    snapshot = GraphSnapshot(
        room_id=room_id,
        graph_state=graph_state
    )
    db.add(snapshot)
    db.flush()

    # snapshot_id 포함해서 다시 build
    graph_state_with_id = build_graph_state(
        db=db,
        graph_snapshot_id=snapshot.graph_snapshot_id,
        room_id=room_id
    )
    graph_state_with_id = _stringify_uuids(graph_state_with_id)
    snapshot.graph_state = graph_state_with_id
    db.flush()
    
    logger.info(f"DB 업데이트 완료 - nodes, edges, assets, graph_snapshots")

    # -------------------------------------------------
    # 10. 이미지 노드 포함 graph_state WS 전송
    # -------------------------------------------------
    await graph_ws_manager.broadcast(room_id, {
        "event": "NODE_IMAGE_UPDATE",
        "core_img_url": None,
        "graph_state": _stringify_uuids(graph_state_with_id)
    })
    logger.info(f"NODE_IMAGE_UPDATE ws 전송")

def _stringify_uuids(obj):
    """
    WS payload에서 UUID 직렬화 문제 방지용.
    """
    if isinstance(obj, dict):
        return {k: _stringify_uuids(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_stringify_uuids(v) for v in obj]
    try:
        # UUID면 str로
        import uuid
        if isinstance(obj, uuid.UUID):
            return str(obj)
    except Exception:
        pass
    return obj

def get_next_category_order(db, room_id: UUID) -> int:
    """
    room 전체에서 CATEGORY 노드들의 최대 order + 1
    """
    last_order = (
        db.query(func.max(CategoryDetail.order))
        .join(Node, Node.node_id == CategoryDetail.node_id)
        .filter(
            Node.room_id == room_id,
            Node.node_type == "CATEGORY"
        )
        .scalar()
    )

    return 0 if last_order is None else last_order + 1