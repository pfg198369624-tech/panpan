import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.services.ai_client import ai_client
from app.core.prompt_manager import prompt_manager
from app.core.config import settings
from app.schemas.validator import AIOutputValidator
from app.models.classification import Classification
from app.models.review import ReviewCleaned
from app.models.finding import Finding
from app.services.monitor import monitor

logger = logging.getLogger(__name__)


class Analyzer:
    async def analyze(self, db: Session, session_id: str) -> int:
        from sqlalchemy import func
        topics = db.query(
            Classification.topic,
            func.count(Classification.id).label("cnt"),
        ).filter(
            Classification.session_id == session_id
        ).group_by(Classification.topic).order_by(func.count(Classification.id).desc()).all()

        total_findings = 0
        for topic_row in topics:
            topic = topic_row.topic
            count = topic_row.cnt
            if count < 2:
                continue

            classifications = db.query(Classification).filter(
                Classification.session_id == session_id,
                Classification.topic == topic,
            ).limit(10).all()

            cleaned_ids = [c.cleaned_id for c in classifications]
            reviews = db.query(ReviewCleaned).filter(ReviewCleaned.id.in_(cleaned_ids)).all()
            reviews_text = "\n".join([
                f"评论{i + 1}: {r.content_clean or ''}"
                for i, r in enumerate(reviews)
            ])

            prompt = prompt_manager.render(
                "analyzer", "v1",
                topic=topic, count=count, reviews_text=reviews_text,
            )
            result = await ai_client.call(prompt, task="analyze")

            monitor.record_ai_call(
                db=db, session_id=session_id, step="5", task="analyze",
                model=settings.volc_model_name,
                prompt_snapshot=prompt, response_snapshot=result.text,
                prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens,
                total_tokens=result.tokens, cost=result.tokens * settings.ai_cost_per_token,
                status="success" if result.success else "failed",
                error_message=result.error, retry_count=result.retry_count,
                duration_ms=result.duration_ms,
            )

            if result.success:
                try:
                    parsed = AIOutputValidator.parse_and_validate(result.text, dict)
                    if isinstance(parsed, list):
                        parsed = parsed[0] if parsed else {}
                    data = parsed if isinstance(parsed, dict) else json.loads(AIOutputValidator.repair_json(result.text))
                    review_ids = [r.id for r in reviews]
                    finding = Finding(
                        session_id=session_id,
                        title=f"Topic: {topic}",
                        description=data.get("core_problem", ""),
                        source_review_ids=json.dumps(review_ids),
                        sample_count=count,
                        confidence="medium" if count >= 5 else "low",
                        conclusion_type="model",
                    )
                    db.add(finding)
                    total_findings += 1
                except Exception as e:
                    logger.error(f"Failed to parse analysis result: {e}")

        db.commit()
        return total_findings


analyzer = Analyzer()
