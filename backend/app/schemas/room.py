from pydantic import BaseModel
from uuid import UUID
from typing import List
from app.schemas.user import UserDTO


class RoomCreate(BaseModel):
    room_topic: str
    password: str
    nickname: str


class RoomListDTO(BaseModel):
    room_id: UUID
    room_topic: str


class RoomInfoDTO(BaseModel):
    room_topic: str
    users: List[UserDTO]