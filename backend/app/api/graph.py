from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.schemas.graph.graph_get_req import GraphGetReq
from app.schemas.graph.graph_resp import GraphResp
from app.services.graph_query import get_current_graph_for_unity
from app.schemas.graph.graph_event_req import GraphEventReq
from app.db.models import GraphVersion, GraphSnapshot

router = APIRouter()

@router.get("", response_model=GraphResp)
def graph_get(req: GraphGetReq, db: Session = Depends(get_db)):
    graph = get_current_graph_for_unity(db, req.session_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph for this session")
    return graph
    
    
    
@router.patch("/event", response_model=GraphResp)
def graph_event_patch(req: GraphEventReq, db: Session = Depends(get_db)):

    gv = (
        db.query(GraphVersion)
        .filter(GraphVersion.session_id == req.session_id)
        .order_by(GraphVersion.version.desc())
        .first()
    )
    if not gv:
        raise HTTPException(status_code=404, detail="No graph for session")

    # JSON-safe dump
    graph_state = req.model_dump(
        include={"root_node","main_graph","sub_graphs"},
        by_alias=True,
        mode="json"   # 🔥 이 줄이 핵심
    )

    graph_state["graph_version_id"] = str(gv.graph_version_id)

    snap = GraphSnapshot(
        graph_version_id=gv.graph_version_id,
        graph_state=graph_state
    )
    db.add(snap)
    db.commit()

    return graph_state