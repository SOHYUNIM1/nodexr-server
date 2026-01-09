from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone


class UtterancesReq(BaseModel):
    session_id: UUID
    user_id: Optional[str] = None
    text: str = Field(min_length=1)
    created_at: Optional[datetime] = None

    def normalized_created_at(self) -> datetime:
        # created_at이 안 오면 서버 시간으로 채움
        if self.created_at is None:
            return datetime.now(timezone.utc)
        # naive면 UTC로 가정(혹은 프로젝트 정책에 맞춰 수정)
        if self.created_at.tzinfo is None:
            return self.created_at.replace(tzinfo=timezone.utc)
        return self.created_at
