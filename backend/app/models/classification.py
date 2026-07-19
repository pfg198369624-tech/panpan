from sqlalchemy import Column, String, Text, Integer, DateTime, BIGINT, ForeignKey, DECIMAL, func
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False)
    cleaned_id = Column(BIGINT, ForeignKey("reviews_cleaned.id"), nullable=False)
    topic = Column(String(128), nullable=False)
    subtopic = Column(String(128))
    sentiment = Column(String(16))
    ai_labeled = Column(TINYINT, default=1)
    confidence = Column(DECIMAL(5, 2))
    created_at = Column(DateTime, server_default=func.now())
