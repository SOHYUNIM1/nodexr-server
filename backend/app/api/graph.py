from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal

#router = APIRouter()
#@router.get("", response_model=GraphResp)
#def graph_get(req: GraphGetReq, db: Session = Depends(get_db)):
    
    
#@router.patch("/event", response_model=GeneralResp)
#def graph_event_patch(req: GraphEventReq, db: Session = Depends(get_db)):