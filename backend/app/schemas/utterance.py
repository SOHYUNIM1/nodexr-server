from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime

class UtteranceIn(BaseModel):
    session_id: UUID
    user_id: Optional[str] = None
    text: str = Field(min_length=1)
    created_at: datetime