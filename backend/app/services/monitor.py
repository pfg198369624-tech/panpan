from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.ai_call_log import AICallLog
from app.models.session import AnalysisSession
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MonitoringService:
    def record_ai_call(self, db: Session, session_id: str, step: str, task: str,
                       model: str, prompt_snapshot: str, response_snapshot: str,
                       prompt_tokens: int, completion_tokens: int, total_tokens: int,
                       cost: float, status: str, error_message: str = "",
                       retry_count: int = 0, duration_ms: int = 0):
        try:
            log = AICallLog(
                session_id=session_id,
                step=step,
                task=task,
                model=model,
                prompt_snapshot=str(prompt_snapshot or "")[:500],
                response_snapshot=str(response_snapshot or "")[:2000],
                prompt_tokens=int(prompt_tokens or 0),
                completion_tokens=int(completion_tokens or 0),
                total_tokens=int(total_tokens or 0),
                cost=float(cost or 0),
                status=status,
                error_message=str(error_message or ""),
                retry_count=int(retry_count or 0),
                duration_ms=int(duration_ms or 0),
            )
            db.add(log)
            db.flush()

            session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
            if session:
                session.total_tokens = (session.total_tokens or 0) + (total_tokens or 0)
                session.total_prompt_tokens = (session.total_prompt_tokens or 0) + (prompt_tokens or 0)
                session.total_completion_tokens = (session.total_completion_tokens or 0) + (completion_tokens or 0)
                session.total_cost = (session.total_cost or 0) + (cost or 0)
                session.ai_call_count = (session.ai_call_count or 0) + 1
                if not status == "success":
                    session.ai_fail_count = (session.ai_fail_count or 0) + 1
                session.ai_retry_count = (session.ai_retry_count or 0) + (retry_count or 0)
            db.commit()
        except Exception as e:
            logger.error(f"record_ai_call failed: {e}")
            db.rollback()

    def get_session_stats(self, db: Session, session_id: str) -> dict:
        session = db.query(AnalysisSession).filter(AnalysisSession.id == session_id).first()
        if not session:
            return {}
        return {
            "total_tokens": session.total_tokens or 0,
            "total_cost": float(session.total_cost or 0),
            "ai_call_count": session.ai_call_count or 0,
            "ai_fail_count": session.ai_fail_count or 0,
            "ai_retry_count": session.ai_retry_count or 0,
            "duration_seconds": session.duration_seconds or 0,
        }


monitor = MonitoringService()
