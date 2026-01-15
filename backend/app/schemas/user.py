from pydantic import BaseModel
from uuid import UUID


class UserCreate(BaseModel):
    room_id: UUID
    nickname: str


class UserDTO(BaseModel):
    nickname: str
    leader: bool