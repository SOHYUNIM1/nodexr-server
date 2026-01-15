from enum import Enum
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

class PhaseType(str, Enum):
    BASIC_DISCUSS = "BASIC_DISCUSS"
    CATEGORY_DISCUSS = "CATEGORY_DISCUSS"

class UtteranceCreate(BaseModel):
    room_id: UUID
    user_id: UUID
    phase: PhaseType
    text: str
    img_url: Optional[str] = None