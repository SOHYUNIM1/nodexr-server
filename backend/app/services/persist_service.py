from sqlalchemy.orm import Session
from uuid import UUID
from app.db import models

def get_latest_snapshot(db: Session, session_id: UUID):
    gv = (
        db.query(models.GraphVersion)
        .filter(models.GraphVersion.session_id == session_id)
        .order_by(models.GraphVersion.version.desc())
        .first()
    )
    if not gv:
        return None, None

    snap = (
        db.query(models.GraphSnapshot)
        .filter(models.GraphSnapshot.graph_version_id == gv.graph_version_id)
        .order_by(models.GraphSnapshot.created_at.desc())
        .first()
    )
    return gv, (snap.graph_state if snap else None)

def get_next_version(db: Session, session_id: UUID) -> int:
    gv = (
        db.query(models.GraphVersion)
        .filter(models.GraphVersion.session_id == session_id)
        .order_by(models.GraphVersion.version.desc())
        .first()
    )
    return (gv.version + 1) if gv else 1

def persist_graph_snapshot(db: Session, session_id: UUID, graph_state: dict):
    # graph_versions 생성 (graph_version_id를 graph_state의 id로 맞춤 → 추적 쉬움)
    next_ver = get_next_version(db, session_id)

    gv = models.GraphVersion(
        graph_version_id=graph_state["graph_version_id"],
        session_id=session_id,
        version=next_ver,
    )
    db.add(gv)
    db.flush()

    snap = models.GraphSnapshot(
        graph_version_id=gv.graph_version_id,
        graph_state=graph_state,
    )
    db.add(snap)