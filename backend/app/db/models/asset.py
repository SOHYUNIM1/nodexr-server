import uuid
from sqlalchemy import Column, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

class Asset(Base):
    __tablename__ = "assets"

    asset_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.node_id", ondelete="CASCADE"), nullable=True)
    category_detail_id = Column(UUID(as_uuid=True), ForeignKey("category_details.category_detail_id", ondelete="CASCADE"), nullable=False)
    img_url = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # 2D_ROOT_CANDIDATE 등
