from sqlalchemy import Column, String, Text, DateTime, BIGINT, func
from app.core.database import Base


class WorkflowLog(Base):
    __tablename__ = "workflow_logs"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False)
    step = Column(String(64), nullable=False)
    status = Column(String(32))
    input_summary = Column(Text)
    output_summary = Column(Text)
    error_message = Column(Text)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
