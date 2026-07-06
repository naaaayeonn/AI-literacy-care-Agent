from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# --- Session ---
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


# --- Quiz (6/25) ---
class QuizSubmitRequest(BaseModel):
    quizId: str
    selectedOption: str


class QuizSubmitResponse(BaseModel):
    correct: bool
    explanation: str
    quiz_id: str


# --- Session Result (6/26) ---
class ScoreSeriesItem(BaseModel):
    label: str
    before: float
    after: float


class BadgeItem(BaseModel):
    id: str
    name: str
    emoji: str
    description: str
    acquiredAt: Optional[str] = None


class SessionResultResponse(BaseModel):
    sessionId: str
    literacyScore: float
    comprehensionScore: float
    engagementScore: float
    difficultyBonus: float = 0.0
    completionRate: float = 100.0
    xpEarned: int = 0
    totalXp: int = 0
    level: int = 1
    scoreSeries: List[ScoreSeriesItem] = []
    badges: List[BadgeItem] = []
    sessionDurationMs: int = 0


# --- Term Explanation / RAG Stub (7/5) ---
class TermExplainRequest(BaseModel):
    term: str


class TermExplainResponse(BaseModel):
    explanation: str


# --- Literacy Profile (6/30) ---
class ProfileResponse(BaseModel):
    user_id: str
    total_sessions: int = 0
    avg_literacy_score: float = 0.0
    avg_comprehension: float = 0.0
    avg_engagement: float = 0.0
    current_level: int = 1
    total_xp: int = 0
    weaknesses: Optional[dict] = None
    strengths: Optional[dict] = None
    trend: str = "stable"


# --- Analytics Summary (7/1) ---
class AnalyticsSummaryResponse(BaseModel):
    user_id: str
    total_sessions: int = 0
    total_reading_time_minutes: float = 0.0
    avg_literacy_score: float = 0.0
    score_trend: List[ScoreSeriesItem] = []
    recent_sessions: List[dict] = []
    level: int = 1
    total_xp: int = 0
