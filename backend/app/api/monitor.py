from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api_response import ApiResponse
from app.models.ai_call_log import AICallLog
from app.models.session import AnalysisSession

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


@router.get("/stats")
async def get_monitor_stats(session_id: str = Query(...), db: Session = Depends(get_db)):
    session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
    if not session:
        return ApiResponse(success=False, error="Session not found")
    return ApiResponse(data={
        "session_id": session.id,
        "total_tokens": session.total_tokens,
        "total_cost": float(session.total_cost or 0),
        "ai_call_count": session.ai_call_count,
        "ai_fail_count": session.ai_fail_count,
        "ai_retry_count": session.ai_retry_count,
        "duration_seconds": session.duration_seconds,
    })


@router.get("/call-logs")
async def get_ai_call_logs(session_id: str = Query(...), db: Session = Depends(get_db)):
    logs = db.query(AICallLog).filter(AICallLog.session_id == session_id).order_by(AICallLog.created_at).all()
    return ApiResponse(data=[{
        "id": l.id,
        "step": l.step,
        "task": l.task,
        "model": l.model,
        "prompt_tokens": l.prompt_tokens,
        "completion_tokens": l.completion_tokens,
        "total_tokens": l.total_tokens,
        "cost": float(l.cost or 0),
        "status": l.status,
        "error_message": l.error_message,
        "retry_count": l.retry_count,
        "duration_ms": l.duration_ms,
    } for l in logs])
