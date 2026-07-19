from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api_request import StartWorkflowRequest
from app.schemas.api_response import ApiResponse
from app.models.session import AnalysisSession
from app.workflow.engine import run_workflow
from app.workflow.websocket import ws_manager
from app.services.collector import collector
from app.core.config import settings
import uuid
from datetime import datetime
import asyncio

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


@router.post("/start")
async def start_workflow(req: StartWorkflowRequest, db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())[:8]
    app_id = ""
    try:
        app_id = collector.extract_app_id(req.app_url)
    except Exception:
        app_id = "unknown"

    session = AnalysisSession(
        id=session_id,
        app_id=app_id,
        app_url=req.app_url,
        user_goal=req.user_goal,
        status="created",
    )
    db.add(session)
    db.commit()

    asyncio.create_task(run_workflow(session_id))

    return ApiResponse(data={"session_id": session_id})


@router.get("/{session_id}/status")
async def get_workflow_status(session_id: str, db: Session = Depends(get_db)):
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        return ApiResponse(success=False, error="Session not found")
    return ApiResponse(data={
        "session_id": session.id,
        "status": session.status,
        "current_step": session.current_step,
        "total_steps": settings.workflow_total_steps,
    })


@router.get("/{session_id}/logs")
async def get_workflow_logs(session_id: str, db: Session = Depends(get_db)):
    from app.models.workflow_log import WorkflowLog
    logs = db.query(WorkflowLog).filter(WorkflowLog.session_id == session_id).order_by(WorkflowLog.started_at).all()
    return ApiResponse(data=[{
        "step": log.step,
        "status": log.status,
        "input_summary": log.input_summary,
        "output_summary": log.output_summary,
        "error_message": log.error_message,
        "started_at": str(log.started_at) if log.started_at else None,
        "finished_at": str(log.finished_at) if log.finished_at else None,
    } for log in logs])


@router.websocket("/{session_id}/ws")
async def workflow_ws(ws: WebSocket, session_id: str):
    await ws_manager.connect(session_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id, ws)


@router.get("/debug/classify/{session_id}")
async def debug_classify(session_id: str, db: Session = Depends(get_db)):
    """Diagnostic: test classifier and return detailed error"""
    import traceback
    from app.services.classifier import classifier as clf
    try:
        count = await clf.classify(db, session_id, batch_size=5)
        return ApiResponse(data={"count": count})
    except Exception as e:
        tb = traceback.format_exc()
        return ApiResponse(success=False, error=str(e), data={"traceback": tb})


@router.get("/sessions")
async def list_sessions(db: Session = Depends(get_db)):
    from sqlalchemy import func as sa_func
    from app.models.prd import PRDRequirement
    from app.models.test_case import TestCase

    sessions = db.query(AnalysisSession).order_by(AnalysisSession.created_at.desc()).limit(50).all()
    session_ids = [s.id for s in sessions]

    prd_counts = dict(
        db.query(PRDRequirement.session_id, sa_func.count(PRDRequirement.id))
        .filter(PRDRequirement.session_id.in_(session_ids))
        .group_by(PRDRequirement.session_id).all()
    )
    tc_counts = dict(
        db.query(TestCase.session_id, sa_func.count(TestCase.id))
        .filter(TestCase.session_id.in_(session_ids))
        .group_by(TestCase.session_id).all()
    )

    return ApiResponse(data=[{
        "id": s.id,
        "app_id": s.app_id,
        "app_name": s.app_name,
        "app_url": s.app_url,
        "user_goal": s.user_goal,
        "status": s.status,
        "current_step": s.current_step,
        "duration_seconds": s.duration_seconds,
        "error_message": s.error_message,
        "created_at": str(s.created_at) if s.created_at else None,
        "prd_count": prd_counts.get(s.id, 0),
        "test_case_count": tc_counts.get(s.id, 0),
    } for s in sessions])


@router.post("/resume/{session_id}")
async def resume_workflow(session_id: str, db: Session = Depends(get_db)):
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        return ApiResponse(success=False, error="Session not found")
    if session.status != "collection_done":
        session.status = "collection_done"
        session.error_message = None
        db.commit()
    asyncio.create_task(run_workflow(session_id))
    return ApiResponse(data={"session_id": session_id})
async def get_session_detail(session_id: str, db: Session = Depends(get_db)):
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        return ApiResponse(success=False, error="Session not found")
    return ApiResponse(data={
        "id": session.id,
        "app_id": session.app_id,
        "app_name": session.app_name,
        "app_url": session.app_url,
        "user_goal": session.user_goal,
        "status": session.status,
        "current_step": session.current_step,
        "total_tokens": session.total_tokens,
        "total_cost": float(session.total_cost or 0),
        "ai_call_count": session.ai_call_count,
        "ai_fail_count": session.ai_fail_count,
        "ai_retry_count": session.ai_retry_count,
        "duration_seconds": session.duration_seconds,
        "error_message": session.error_message,
    })
