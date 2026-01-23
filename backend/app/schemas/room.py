import datetime
from pydantic import BaseModel
from uuid import UUID
from typing import List, Union
from app.schemas.user import UserDTO


class RoomCreate(BaseModel):
    room_topic: str
    password: str
    nickname: str

class RoomReenterReq(BaseModel):
    room_id: UUID

RoomGenerateReq = Union[RoomCreate, RoomReenterReq]

class RoomListDTO(BaseModel):
    room_id: UUID
    room_topic: str
    created_at: str


class RoomInfoDTO(BaseModel):
    room_topic: str
    users: List[UserDTO]