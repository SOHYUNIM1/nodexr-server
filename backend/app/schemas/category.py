from uuid import UUID
from pydantic import BaseModel

class CategoryListResp(BaseModel):
    category_id: UUID
    category_name: str

class CategorySelectReq(BaseModel):
    room_id: UUID
    category_id: UUID