import uuid
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base

class GraphSnapshot(Base):
    __tablename__ = "graph_snapshots"

    graph_snapshot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.room_id", ondelete="CASCADE"), nullable=False)
    graph_state = Column(JSONB, nullable=False)
    created_at = Column(DateTime, server_default=func.now())