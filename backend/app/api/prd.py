from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api_response import ApiResponse
from app.models.prd import PRDVersion, PRDRequirement

router = APIRouter(prefix="/api/prd", tags=["prd"])


@router.get("/versions")
async def get_prd_versions(session_id: str = Query(...), db: Session = Depends(get_db)):
    versions = db.query(PRDVersion).filter(PRDVersion.session_id == session_id).order_by(PRDVersion.priority).all()
    return ApiResponse(data=[{
        "id": v.id,
        "version_no": v.version_no,
        "name": v.name,
        "priority": v.priority,
        "status": v.status,
    } for v in versions])


@router.get("/requirements")
async def get_prd_requirements(session_id: str = Query(...), db: Session = Depends(get_db)):
    items = db.query(PRDRequirement).filter(PRDRequirement.session_id == session_id).all()
    return ApiResponse(data=[{
        "id": r.id,
        "req_id": r.req_id,
        "version_id": r.version_id,
        "title": r.title,
        "description": r.description,
        "priority": r.priority,
        "source_finding_ids": r.source_finding_ids,
        "status": r.status,
    } for r in items])
