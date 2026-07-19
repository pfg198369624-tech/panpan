from sqlalchemy import Column, String, Text, Integer, DateTime, DECIMAL, func
from app.core.database import Base


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String(64), primary_key=True)
    app_id = Column(String(64), nullable=False)
    app_name = Column(String(255))
    app_url = Column(Text, nullable=False)
    user_goal = Column(Text)
    status = Column(String(32), default="created")
    current_step = Column(Integer, default=0)
    ai_model = Column(String(128))
    total_tokens = Column(Integer, default=0)
    total_cost = Column(DECIMAL(10, 6), default=0)
    total_prompt_tokens = Column(Integer, default=0)
    total_completion_tokens = Column(Integer, default=0)
    ai_call_count = Column(Integer, default=0)
    ai_fail_count = Column(Integer, default=0)
    ai_retry_count = Column(Integer, default=0)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    duration_seconds = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
