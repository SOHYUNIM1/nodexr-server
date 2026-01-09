import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base

class XRSession(Base):
    __tablename__ = "xr_sessions"
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phase = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Utterance(Base):
    __tablename__ = "utterances"
    utterance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("xr_sessions.session_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class GraphVersion(Base):
    __tablename__ = "graph_versions"
    graph_version_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("xr_sessions.session_id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GraphSnapshot(Base):
    __tablename__ = "graph_snapshots"
    snapshot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_version_id = Column(UUID(as_uuid=True), ForeignKey("graph_versions.graph_version_id", ondelete="CASCADE"), nullable=False)
    graph_state = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GraphLock(Base):
    __tablename__ = "graph_locks"
    session_id = Column(UUID(as_uuid=True), ForeignKey("xr_sessions.session_id", ondelete="CASCADE"), primary_key=True)
    locked_by = Column(String)
    locked_at = Column(DateTime(timezone=True))
    lock_version = Column(Integer, nullable=False, default=0)