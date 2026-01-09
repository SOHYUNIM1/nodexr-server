from pydantic import BaseModel, Field

class GeneralResp(BaseModel):
    message : str = Field(min_length=1)