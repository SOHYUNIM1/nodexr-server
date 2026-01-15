from pydantic import BaseModel
from uuid import UUID

class Select2DRequest(BaseModel):
    room_id: UUID
    node_id: UUID