from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.sql import func
from ..core.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReadingSession(Base):
    __tablename__ = "reading_sessions"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    document_id = Column(String)
    literacy_score = Column(Float, nullable=True)
    comprehension_score = Column(Float, nullable=True)
    engagement_score = Column(Float, nullable=True)
    difficulty_score = Column(Float, nullable=True, default=50.0)
    readability_score = Column(Float, nullable=True, default=50.0)  # 2번 이독성(독립변수)
    literacy_domains = Column(JSON, nullable=True)  # 문해 5대 지표(레이더용) {comprehension,focus,closeReading,challenge,stability}
    xp_earned = Column(Integer, nullable=True, default=0)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)


class ReadingEvent(Base):
    __tablename__ = "reading_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("reading_sessions.id"))
    event_type = Column(String)
    timestamp_ms = Column(Integer)
    metadata_json = Column(JSON, nullable=True)


class QuizResult(Base):
    """퀴즈 제출 결과 테이블 (6/25)"""
    __tablename__ = "quiz_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("reading_sessions.id"))
    quiz_id = Column(String, index=True)
    question = Column(Text, nullable=True)
    selected_option = Column(String)
    correct_option = Column(String, nullable=True)
    is_correct = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LiteracyProfile(Base):
    """장기 리터러시 프로필 테이블 (6/30)"""
    __tablename__ = "literacy_profiles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, index=True)
    total_sessions = Column(Integer, default=0)
    avg_literacy_score = Column(Float, default=0.0)
    avg_comprehension = Column(Float, default=0.0)
    avg_engagement = Column(Float, default=0.0)
    current_level = Column(Integer, default=1)
    total_xp = Column(Integer, default=0)
    weaknesses = Column(JSON, nullable=True)  # JSONB: {"vocabulary": 0.3, "speed": 0.7, ...}
    strengths = Column(JSON, nullable=True)
    trend = Column(String, default="stable")  # improving, stable, declining
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
