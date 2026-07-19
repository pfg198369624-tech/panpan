import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings

logger = logging.getLogger(__name__)


class ReflectionEngine:
    def __init__(self, session_id: str):
        self.session_id = session_id

    def reflect(self, step: int, output: dict) -> dict:
        result = {"passed": True, "reason": None, "should_retry": False}

        if step == 2 and output.get("count", 0) < 5:
            result["passed"] = False
            result["reason"] = f"Only {output.get('count', 0)} reviews collected, minimum 5 required"
            result["should_retry"] = True

        elif step == 3 and output.get("noise_ratio", 0) > 0.8:
            result["passed"] = False
            result["reason"] = f"Noise ratio too high: {output.get('noise_ratio', 0):.1%}"
            result["should_retry"] = True

        elif step == 5:
            finding_count = output.get("findings", 0)
            if finding_count == 0:
                result["passed"] = False
                result["reason"] = "No findings generated from evidence"
                result["should_retry"] = True

        elif step == 4:
            topic_count = output.get("topics", 0)
            if topic_count == 0:
                result["passed"] = False
                result["reason"] = "No topics generated from classification"
                result["should_retry"] = True

        elif step == 8:
            issues = output.get("issues", 0)
            if issues > 0:
                result["passed"] = False
                result["reason"] = f"Traceability validation found {issues} issues"
                result["should_retry"] = False

        return result

    def can_retry(self, step: int, attempt: int, max_retries: int = None) -> bool:
        if max_retries is None:
            max_retries = settings.workflow_max_retry_per_step
        return attempt < max_retries
