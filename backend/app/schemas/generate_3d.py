from pydantic import BaseModel
from uuid import UUID

class Generate3DRequest(BaseModel):
    room_id: UUID
    asset_id: UUID