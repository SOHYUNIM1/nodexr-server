# services/graph_query.py
from sqlalchemy.orm import Session
from uuid import UUID
from app.db import models
from app.services.graph_core import project_to_unity

def get_current_graph_for_unity(db: Session, session_id: UUID):
    # 1) 최신 graph_version
    gv = (
        db.query(models.GraphVersion)
        .filter(models.GraphVersion.session_id == session_id)
        .order_by(models.GraphVersion.version.desc())
        .first()
    )
    if not gv:
        return None

    # 2) 그 버전의 최신 snapshot
    snap = (
        db.query(models.GraphSnapshot)
        .filter(models.GraphSnapshot.graph_version_id == gv.graph_version_id)
        .order_by(models.GraphSnapshot.created_at.desc())
        .first()
    )
    if not snap:
        return None

    # 3) 내부 graph_state → Unity GraphResp로 projection
    return project_to_unity(snap.graph_state)