import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

class Category(Base):
    __tablename__ = "categories"

    category_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.room_id", ondelete="CASCADE"), nullable=False)
    category_name = Column(String, nullable=False)
    phase = Column(String, nullable=False, default="INACTIVE")  #ACTIVE / INACTIVE
