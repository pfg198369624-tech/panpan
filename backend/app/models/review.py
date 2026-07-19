from sqlalchemy import Column, String, Text, Integer, DateTime, BIGINT, ForeignKey, func
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base


class ReviewRaw(Base):
    __tablename__ = "reviews_raw"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False)
    app_id = Column(String(64), nullable=False)
    review_id = Column(String(128), nullable=False)
    author = Column(String(255))
    rating = Column(TINYINT, nullable=False)
    title = Column(Text)
    content = Column(Text, nullable=False)
    version = Column(String(64))
    country = Column(String(8), default="us")
    reviewed_at = Column(DateTime)
    collected_at = Column(DateTime, server_default=func.now())
    source = Column(String(32), default="rss")


class ReviewCleaned(Base):
    __tablename__ = "reviews_cleaned"

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False)
    raw_id = Column(BIGINT, ForeignKey("reviews_raw.id"), nullable=False)
    content_clean = Column(Text)
    language = Column(String(16))
    is_duplicate = Column(TINYINT, default=0)
    duplicate_group = Column(String(64))
    is_noise = Column(TINYINT, default=0)
    created_at = Column(DateTime, server_default=func.now())
