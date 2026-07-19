from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api_response import ApiResponse
from app.models.test_case import TestCase

router = APIRouter(prefix="/api/test-cases", tags=["test-cases"])


@router.get("")
async def get_test_cases(session_id: str = Query(...), db: Session = Depends(get_db)):
    items = db.query(TestCase).filter(TestCase.session_id == session_id).all()
    return ApiResponse(data=[{
        "id": t.id,
        "case_id": t.case_id,
        "req_id": t.req_id,
        "title": t.title,
        "preconditions": t.preconditions,
        "steps": t.steps,
        "expected_result": t.expected_result,
        "source_review_ids": t.source_review_ids,
        "status": t.status,
    } for t in items])
