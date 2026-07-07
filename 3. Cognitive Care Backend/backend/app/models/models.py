from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
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
    
    # 누적된 스코어 및 최종 결과
    literacy_score = Column(Float, nullable=True)
    comprehension_score = Column(Float, nullable=True)
    engagement_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

class ReadingEvent(Base):
    __tablename__ = "reading_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("reading_sessions.id"))
    event_type = Column(String) # scroll, blur, focus, pause
    timestamp_ms = Column(Integer)
    metadata_json = Column(JSON, nullable=True)
