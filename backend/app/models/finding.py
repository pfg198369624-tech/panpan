from sqlalchemy import Column, String, Text, Integer, DateTime, BIGINT, JSON, func
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base


class Finding(Base):
    __tablename__ = "findings"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    source_review_ids = Column(JSON)
    sample_count = Column(Integer, default=0)
    confidence = Column(String(32))
    conflicting_evidence = Column(Text)
    conclusion_type = Column(String(32))
    is_confirmed = Column(TINYINT, default=0)
    created_at = Column(DateTime, server_default=func.now())
