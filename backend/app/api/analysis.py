from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api_response import ApiResponse
from app.models.classification import Classification
from app.models.finding import Finding
from app.models.session import AnalysisSession

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/classifications")
async def get_classifications(session_id: str = Query(...), db: Session = Depends(get_db)):
    items = db.query(Classification).filter(Classification.session_id == session_id).all()
    return ApiResponse(data=[{
        "id": c.id,
        "topic": c.topic,
        "subtopic": c.subtopic,
        "sentiment": c.sentiment,
        "confidence": float(c.confidence) if c.confidence else None,
    } for c in items])


@router.get("/findings")
async def get_findings(session_id: str = Query(...), db: Session = Depends(get_db)):
    items = db.query(Finding).filter(Finding.session_id == session_id).all()
    return ApiResponse(data=[{
        "id": f.id,
        "title": f.title,
        "description": f.description,
        "source_review_ids": f.source_review_ids,
        "sample_count": f.sample_count,
        "confidence": f.confidence,
        "conflicting_evidence": f.conflicting_evidence,
        "conclusion_type": f.conclusion_type,
    } for f in items])


@router.get("/scope")
async def get_analysis_scope(session_id: str = Query(...), db: Session = Depends(get_db)):
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        return ApiResponse(success=False, error="Session not found")
    return ApiResponse(data={
        "scope_description": session.user_goal or "General analysis of all reviews",
        "app_id": session.app_id,
        "app_url": session.app_url,
    })
