from pydantic import BaseModel
from uuid import UUID

class Generate3DRequest(BaseModel):
    room_id: UUID
    img_url: str