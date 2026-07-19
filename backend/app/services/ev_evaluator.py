import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.services.ai_client import ai_client
from app.core.prompt_manager import prompt_manager
from app.core.config import settings
from app.schemas.validator import AIOutputValidator
from app.models.finding import Finding
from app.models.review import ReviewCleaned, ReviewRaw
from app.services.monitor import monitor

logger = logging.getLogger(__name__)


class EvidenceEvaluator:
    async def evaluate(self, db: Session, session_id: str) -> int:
        findings = db.query(Finding).filter(
            Finding.session_id == session_id,
            Finding.conclusion_type == "model",
        ).all()

        total = 0
        for finding in findings:
            updated = await self._evaluate_one(db, session_id, finding)
            if updated:
                total += 1
        return total

    async def _evaluate_one(self, db: Session, session_id: str, finding: Finding) -> bool:
        review_ids = []
        if finding.source_review_ids:
            try:
                review_ids = json.loads(finding.source_review_ids) if isinstance(finding.source_review_ids, str) else finding.source_review_ids
            except Exception:
                review_ids = []

        supporting = []
        cleans = db.query(ReviewCleaned).filter(ReviewCleaned.id.in_(review_ids)).all() if review_ids else []
        for c in cleans:
            raw = db.query(ReviewRaw).filter(ReviewRaw.id == c.raw_id).first()
            if raw and raw.rating >= 3:
                supporting.append(c.content_clean or "")

        prompt = prompt_manager.render(
            "evaluator", "v1",
            topic=finding.title,
            supporting_reviews="\n".join(supporting[:5]) if supporting else "无支持评论",
            opposing_reviews="无",
        )
        result = await ai_client.call(prompt, task="evaluate")

        monitor.record_ai_call(
            db=db, session_id=session_id, step="5", task="evaluate",
            model=settings.volc_model_name,
            prompt_snapshot=prompt, response_snapshot=result.text,
            prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens,
            total_tokens=result.tokens, cost=result.tokens * settings.ai_cost_per_token,
            status="success" if result.success else "failed",
            retry_count=result.retry_count, duration_ms=result.duration_ms,
        )

        if result.success:
            try:
                data = json.loads(AIOutputValidator.repair_json(result.text))
                finding.confidence = data.get("confidence", "low")
                finding.conflicting_evidence = data.get("conflicting_feedback")
                finding.sample_count = len(review_ids)
                finding.conclusion_type = "model" if data.get("evidence_sufficient", False) else "assumption"
                db.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to parse evaluation: {e}")
        return False


ev_evaluator = EvidenceEvaluator()
