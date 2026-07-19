from sqlalchemy import Column, String, Text, Integer, DateTime, BIGINT, JSON, ForeignKey, func
from app.core.database import Base


class PRDVersion(Base):
    __tablename__ = "prd_versions"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False)
    version_no = Column(String(32), nullable=False)
    name = Column(String(128))
    priority = Column(Integer, default=0)
    status = Column(String(32), default="planned")
    created_at = Column(DateTime, server_default=func.now())


class PRDRequirement(Base):
    __tablename__ = "prd_requirements"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False)
    version_id = Column(BIGINT, ForeignKey("prd_versions.id"), nullable=False)
    req_id = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(String(16), default="medium")
    source_finding_ids = Column(JSON)
    status = Column(String(32), default="draft")
    created_at = Column(DateTime, server_default=func.now())
