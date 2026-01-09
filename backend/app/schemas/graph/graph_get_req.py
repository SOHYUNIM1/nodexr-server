from pydantic import BaseModel

class GraphGetReq(BaseModel):
    session_id : str