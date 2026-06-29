from pydantic import BaseModel
from typing import Optional

class SessionStartRequest(BaseModel):
    user_id: str
    document_id: str

class SessionStartResponse(BaseModel):
    session_id: str
    message: str

class SessionFinishRequest(BaseModel):
    literacy_score: Optional[float] = None
    comprehension_score: Optional[float] = None
    engagement_score: Optional[float] = None

class SessionFinishResponse(BaseModel):
    session_id: str
    message: str
    saved_events_count: int
