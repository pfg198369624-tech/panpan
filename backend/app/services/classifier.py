import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.services.ai_client import ai_client
from app.core.config import settings
from app.core.prompt_manager import prompt_manager
from app.schemas.validator import AIOutputValidator
from app.schemas.ai_output import ClassificationOutput
from app.models.review import ReviewCleaned, ReviewRaw
from app.models.classification import Classification
from app.services.monitor import monitor

logger = logging.getLogger(__name__)


class Classifier:
    async def classify(self, db: Session, session_id: str, batch_size: int = None) -> int:
        if batch_size is None:
            batch_size = settings.classifier_batch_size

        # Get all non-noise reviews
        all_reviews = db.query(ReviewCleaned).filter(
            ReviewCleaned.session_id == session_id,
            ReviewCleaned.is_noise == 0,
        ).all()

        # Skip reviews that already have classifications
        existing = {
            r.cleaned_id for r in db.query(Classification.cleaned_id).filter(
                Classification.session_id == session_id
            ).all()
        }
        reviews = [r for r in all_reviews if r.id not in existing]

        if not reviews:
            logger.info(f"All {len(all_reviews)} reviews already classified")
            return len(all_reviews)

        total = 0
        errors = 0
        for i in range(0, len(reviews), batch_size):
            batch = reviews[i:i + batch_size]
            try:
                count = await self._classify_batch(db, session_id, batch)
                total += count
            except Exception as e:
                errors += 1
                logger.error(f"Batch {i // batch_size} failed (continuing): {e}")
                # Batch failed, continue to next batch
                continue
        if errors:
            logger.warning(f"Classifier: {total} classified, {errors} batches failed")
        return total

    async def _classify_batch(self, db: Session, session_id: str, batch: list) -> int:
        reviews_json = json.dumps([
            {"index": idx, "content": r.content_clean or "", "rating": self._get_rating(db, r.id)}
            for idx, r in enumerate(batch)
        ], ensure_ascii=False)

        prompt = prompt_manager.render("classifier", "v1", reviews_json=reviews_json)
        result = await ai_client.call(prompt, task="classify")

        monitor.record_ai_call(
            db=db, session_id=session_id, step="4", task="classify",
            model=settings.volc_model_name,
            prompt_snapshot=prompt, response_snapshot=result.text,
            prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens,
            total_tokens=result.tokens, cost=result.tokens * settings.ai_cost_per_token,
            status="success" if result.success else "failed",
            error_message=result.error, retry_count=result.retry_count,
            duration_ms=result.duration_ms,
        )

        if not result.success:
            raise Exception(f"AI classification API call failed: {result.error}")

        parsed = AIOutputValidator.parse_and_validate(result.text, ClassificationOutput)
        if not parsed:
            raise Exception(f"AI classification parse failed, response:\n{result.text[:200]}")

        items = parsed if isinstance(parsed, list) else [parsed]
        count = 0
        for item in items:
            if item.review_index < len(batch):
                cls = Classification(
                    session_id=session_id,
                    cleaned_id=batch[item.review_index].id,
                    topic=item.topic,
                    subtopic=item.subtopic,
                    sentiment=item.sentiment,
                    confidence=item.confidence,
                )
                db.add(cls)
                count += 1
        db.commit()
        return count

    def _get_rating(self, db: Session, cleaned_id: int) -> int:
        cleaned = db.query(ReviewCleaned).filter(ReviewCleaned.id == cleaned_id).first()
        if cleaned:
            raw = db.query(ReviewRaw).filter(ReviewRaw.id == cleaned.raw_id).first()
            if raw:
                return raw.rating
        return 0


classifier = Classifier()
