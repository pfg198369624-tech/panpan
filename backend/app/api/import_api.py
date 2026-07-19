import asyncio
from fastapi import APIRouter, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api_response import ApiResponse
from app.services.importer import importer
from app.models.session import AnalysisSession
from app.workflow.engine import run_workflow
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/import", tags=["import"])


async def _do_import(db: Session, session_id: str, app_id: str,
                     content: str, file_type: str) -> dict:
    session = AnalysisSession(
        id=session_id,
        app_id=app_id or "imported",
        app_url="",
        user_goal="",
        status="collection_done",
        created_at=datetime.now(),
    )
    db.add(session)
    db.commit()

    if file_type == "json":
        count = importer.import_json(db, session_id, content)
    else:
        count = importer.import_csv(db, session_id, content)

    asyncio.create_task(run_workflow(session_id))
    return {"session_id": session_id, "imported": count}


@router.post("/json")
async def import_json(file: UploadFile = File(...),
                      session_id: str = Form(""),
                      app_id: str = Form(""),
                      db: Session = Depends(get_db)):
    content = (await file.read()).decode("utf-8")
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
    result = await _do_import(db, session_id, app_id, content, "json")
    return ApiResponse(data={**result, "file": file.filename})


@router.post("/csv")
async def import_csv(file: UploadFile = File(...),
                     session_id: str = Form(""),
                     app_id: str = Form(""),
                     db: Session = Depends(get_db)):
    content = (await file.read()).decode("utf-8")
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
    result = await _do_import(db, session_id, app_id, content, "csv")
    return ApiResponse(data={**result, "file": file.filename})
