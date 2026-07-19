from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api_response import ApiResponse
from app.models.review import ReviewRaw, ReviewCleaned

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("/raw")
async def get_raw_reviews(session_id: str = Query(...), db: Session = Depends(get_db)):
    reviews = db.query(ReviewRaw).filter(ReviewRaw.session_id == session_id).all()
    return ApiResponse(data=[{
        "id": r.id,
        "review_id": r.review_id,
        "author": r.author,
        "rating": r.rating,
        "title": r.title,
        "content": r.content,
        "version": r.version,
        "reviewed_at": str(r.reviewed_at) if r.reviewed_at else None,
        "source": r.source,
    } for r in reviews])


@router.get("/cleaned")
async def get_cleaned_reviews(session_id: str = Query(...), db: Session = Depends(get_db)):
    reviews = db.query(ReviewCleaned).filter(ReviewCleaned.session_id == session_id).all()
    return ApiResponse(data=[{
        "id": r.id,
        "raw_id": r.raw_id,
        "content_clean": r.content_clean,
        "language": r.language,
        "is_duplicate": r.is_duplicate,
        "is_noise": r.is_noise,
    } for r in reviews])
