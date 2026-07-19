import json
import logging
from sqlalchemy.orm import Session
from app.services.ai_client import ai_client
from app.core.prompt_manager import prompt_manager
from app.core.config import settings
from app.schemas.validator import AIOutputValidator
from app.schemas.ai_output import SinglePassOutput, ClassificationOutput, AnalysisFindingItem
from app.models.review import ReviewCleaned
from app.models.classification import Classification
from app.models.finding import Finding
from app.services.monitor import monitor

logger = logging.getLogger(__name__)


class SinglePassAnalyzer:
    async def analyze(self, db: Session, session_id: str, user_goal: str) -> dict:
        reviews = db.query(ReviewCleaned).filter(
            ReviewCleaned.session_id == session_id,
            ReviewCleaned.is_noise == 0,
        ).all()
        if not reviews:
            logger.info(f"Session {session_id}: no reviews for analysis")
            return {"classifications": 0, "findings": 0}

        logger.info(f"Session {session_id}: building reviews_json for {len(reviews)} reviews")
        reviews_json = json.dumps([
            {
                "index": idx,
                "content": (r.content_clean or "")[:200],
                "rating": self._get_rating(db, r.id),
            }
            for idx, r in enumerate(reviews)
        ], ensure_ascii=False)
        logger.info(f"Session {session_id}: reviews_json built, calling AI")

        prompt = prompt_manager.render(
            "analysis", "v1",
            user_goal=user_goal,
            total_reviews=len(reviews),
            reviews_json=reviews_json,
        )

        result = await ai_client.call(prompt, task="analysis")
        logger.info(f"Session {session_id}: AI call returned success={result.success}")

        monitor.record_ai_call(
            db=db, session_id=session_id, step="4", task="analysis",
            model=settings.volc_model_name,
            prompt_snapshot=prompt, response_snapshot=result.text,
            prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens,
            total_tokens=result.tokens, cost=result.tokens * settings.ai_cost_per_token,
            status="success" if result.success else "failed",
            error_message=result.error, retry_count=result.retry_count,
            duration_ms=result.duration_ms,
        )
        logger.info(f"Session {session_id}: AI call recorded")

        if not result.success:
            logger.error(f"Single-pass analysis API call failed: {result.error}")
            return {"classifications": 0, "findings": 0}

        logger.info(f"Session {session_id}: parsing result")
        data = self._parse_result(result.text)
        if not data:
            logger.error("Single-pass analysis output validation failed")
            return {"classifications": 0, "findings": 0}

        logger.info(f"Session {session_id}: saving {len(data.classifications)} classifications and {len(data.findings)} findings")
        cls_count = self._save_classifications(db, session_id, reviews, data.classifications)
        fnd_count = self._save_findings(db, session_id, reviews, data.findings)
        logger.info(f"Session {session_id}: saved {cls_count} classifications, {fnd_count} findings, committing")
        db.commit()
        logger.info(f"Session {session_id}: analysis complete")
        return {"classifications": cls_count, "findings": fnd_count}

    def _parse_result(self, text: str) -> SinglePassOutput | None:
        try:
            raw = AIOutputValidator.repair_json(text)
            data = json.loads(raw)
        except Exception as e:
            logger.error(f"Failed to parse AI result JSON: {e}")
            return None

        classifications = []
        for item in data.get("classifications", []):
            try:
                classifications.append(ClassificationOutput(**item))
            except Exception as e:
                logger.warning(f"Dropping invalid classification: {e} | item={item}")

        findings = []
        for item in data.get("findings", []):
            try:
                findings.append(AnalysisFindingItem(**item))
            except Exception as e:
                logger.warning(f"Dropping invalid finding: {e} | item={item}")

        if not classifications and not findings:
            logger.error("No valid classifications or findings after parsing")
            return None

        logger.info(f"Parsed: {len(classifications)} classifications, {len(findings)} findings")
        return SinglePassOutput(classifications=classifications, findings=findings)

    def _save_classifications(self, db: Session, session_id: str,
                               reviews: list, items: list) -> int:
        count = 0
        for item in items:
            if item.review_index is None or item.review_index >= len(reviews):
                continue
            cls = Classification(
                session_id=session_id,
                cleaned_id=reviews[item.review_index].id,
                topic=item.topic or "",
                subtopic=item.subtopic,
                sentiment=item.sentiment or "neutral",
                confidence=item.confidence or 0.5,
            )
            db.add(cls)
            count += 1
        return count

    def _save_findings(self, db: Session, session_id: str,
                       reviews: list, items: list) -> int:
        count = 0
        for item in items:
            review_ids = []
            for idx in (item.source_review_indices or []):
                if idx < len(reviews):
                    review_ids.append(reviews[idx].id)
            finding = Finding(
                session_id=session_id,
                title=item.title or "未命名发现",
                description=item.description or "",
                source_review_ids=json.dumps(review_ids),
                sample_count=len(review_ids),
                confidence=item.confidence or "medium",
                conflicting_evidence=item.conflicting_evidence,
                conclusion_type="model",
            )
            db.add(finding)
            count += 1
        return count

    def _get_rating(self, db: Session, cleaned_id: int) -> int:
        from app.models.review import ReviewRaw
        cleaned = db.get(ReviewCleaned, cleaned_id)
        if cleaned:
            raw = db.get(ReviewRaw, cleaned.raw_id)
            if raw:
                return raw.rating
        return 0


single_pass = SinglePassAnalyzer()
