from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.schemas.graph.graph_get_req import GraphGetReq
from app.schemas.graph.graph_resp import GraphResp
from app.services.graph_query import get_current_graph_for_unity

router = APIRouter()

@router.get("", response_model=GraphResp)
def graph_get(req: GraphGetReq, db: Session = Depends(get_db)):
    graph = get_current_graph_for_unity(db, req.session_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="No graph for this session")
    return graph
    
    
    
#@router.patch("/event", response_model=GeneralResp)
#def graph_event_patch(req: GraphEventReq, db: Session = Depends(get_db)):