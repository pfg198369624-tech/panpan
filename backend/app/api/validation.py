from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api_response import ApiResponse
from app.services.validator import validator

router = APIRouter(prefix="/api/validation", tags=["validation"])


@router.get("/report")
async def get_validation_report(session_id: str = Query(...), db: Session = Depends(get_db)):
    report = validator.validate_traceability(db, session_id)
    return ApiResponse(data=report)
