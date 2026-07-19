from sqlalchemy import Column, String, Text, Integer, DateTime, BIGINT, DECIMAL, func
from app.core.database import Base


class AICallLog(Base):
    __tablename__ = "ai_call_logs"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False)
    step = Column(String(64))
    task = Column(String(64))
    model = Column(String(128))
    prompt_snapshot = Column(Text)
    response_snapshot = Column(Text)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(DECIMAL(10, 6), default=0)
    status = Column(String(32))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
