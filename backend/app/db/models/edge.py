import uuid
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

class Edge(Base):
    __tablename__ = "edges"

    edge_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id", ondelete="CASCADE"), nullable=False)
    to_node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id", ondelete="CASCADE"), nullable=False)