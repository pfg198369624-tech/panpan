import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.services.ai_client import ai_client
from app.core.prompt_manager import prompt_manager
from app.core.config import settings
from app.schemas.validator import AIOutputValidator
from app.schemas.ai_output import TestCaseListOutput, TestCaseOutput
from app.models.prd import PRDRequirement
from app.models.test_case import TestCase
from app.services.monitor import monitor

logger = logging.getLogger(__name__)


class TestGenerator:
    async def generate(self, db: Session, session_id: str) -> int:
        requirements = db.query(PRDRequirement).filter(
            PRDRequirement.session_id == session_id
        ).all()
        if not requirements:
            return 0

        total = 0
        for req in requirements:
            count = await self._generate_for_req(db, session_id, req)
            total += count
        return total

    async def _generate_for_req(self, db: Session, session_id: str, req: PRDRequirement) -> int:
        prompt = prompt_manager.render(
            "test_generator", "v1",
            req_title=req.title,
            req_description=req.description or "",
            source_reviews="用户评论 ID: " + str(req.source_finding_ids),
        )
        result = await ai_client.call(prompt, task="test_generate")

        monitor.record_ai_call(
            db=db, session_id=session_id, step="7", task="test_generate",
            model=settings.volc_model_name,
            prompt_snapshot=prompt, response_snapshot=result.text,
            prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens,
            total_tokens=result.tokens, cost=result.tokens * settings.ai_cost_per_token,
            status="success" if result.success else "failed",
            error_message=result.error, retry_count=result.retry_count,
            duration_ms=result.duration_ms,
        )

        if not result.success:
            return 0

        parsed = AIOutputValidator.parse_and_validate(result.text, TestCaseListOutput)
        if not parsed:
            parsed = AIOutputValidator.parse_and_validate(result.text, TestCaseOutput)
            if not parsed:
                return 0

        items = parsed.test_cases if hasattr(parsed, "test_cases") else [parsed]
        count = 0
        for tc in items:
            test_case = TestCase(
                session_id=session_id,
                case_id=tc.case_id,
                req_id=req.req_id,
                title=tc.title,
                preconditions=tc.preconditions,
                steps=json.dumps(tc.steps),
                expected_result=tc.expected_result,
                source_review_ids=json.dumps(tc.source_review_ids),
            )
            db.add(test_case)
            count += 1

        db.commit()
        return count


test_generator = TestGenerator()
