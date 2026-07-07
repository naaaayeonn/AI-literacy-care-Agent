from pydantic import BaseModel
from typing import Optional

class SessionStartRequest(BaseModel):
    userId: str
    articleId: Optional[str] = None
    content: Optional[list[str]] = None
    source: Optional[dict] = None

class SessionStartResponse(BaseModel):
    sessionId: str
    article: dict
    wsEndpoint: str

class SessionFinishRequest(BaseModel):
    literacy_score: Optional[float] = None
    comprehension_score: Optional[float] = None
    engagement_score: Optional[float] = None

class SessionFinishResponse(BaseModel):
    session_id: str
    message: str
    saved_events_count: int

class EventItem(BaseModel):
    type: str
    timestamp_ms: int
    duration_ms: Optional[int] = None
    position: Optional[float] = None

class EventsRequestModel(BaseModel):
    events: list[EventItem]
