import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.session import Base


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_topic = Column(String, nullable=False)
    password = Column(String, nullable=False)
    phase = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())