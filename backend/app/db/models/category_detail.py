import uuid
from sqlalchemy import Column, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

class CategoryDetail(Base):
    __tablename__ = "category_details"

    category_detail_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.category_id", ondelete="CASCADE"), nullable=False)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id", ondelete="CASCADE"), nullable=False)
    detail_text = Column(Text, nullable=False)
    order = Column(Integer, nullable=False, default=0)
