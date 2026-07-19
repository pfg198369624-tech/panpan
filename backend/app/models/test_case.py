from sqlalchemy import Column, String, Text, DateTime, BIGINT, JSON, func
from app.core.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False)
    case_id = Column(String(32), nullable=False)
    req_id = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False)
    preconditions = Column(Text)
    steps = Column(JSON)
    expected_result = Column(Text)
    source_review_ids = Column(JSON)
    status = Column(String(32), default="draft")
    created_at = Column(DateTime, server_default=func.now())
