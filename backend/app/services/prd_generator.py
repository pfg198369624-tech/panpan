import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.services.ai_client import ai_client
from app.core.prompt_manager import prompt_manager
from app.core.config import settings
from app.schemas.validator import AIOutputValidator
from app.schemas.ai_output import PRDOutput, PRDVersionOutput
from app.models.finding import Finding
from app.models.prd import PRDVersion, PRDRequirement
from app.services.monitor import monitor

logger = logging.getLogger(__name__)


class PRDGenerator:
    async def generate(self, db: Session, session_id: str) -> int:
        findings = db.query(Finding).filter(
            Finding.session_id == session_id,
            Finding.conclusion_type != "assumption",
        ).all()
        if not findings:
            return 0

        findings_json = json.dumps([
            {"id": f.id, "title": f.title, "description": f.description,
             "confidence": f.confidence, "sample_count": f.sample_count}
            for f in findings
        ], ensure_ascii=False, indent=2)

        prompt = prompt_manager.render("prd_generator", "v1", findings_json=findings_json)
        result = await ai_client.call(prompt, task="prd_generate")

        monitor.record_ai_call(
            db=db, session_id=session_id, step="6", task="prd_generate",
            model=settings.volc_model_name,
            prompt_snapshot=prompt, response_snapshot=result.text,
            prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens,
            total_tokens=result.tokens, cost=result.tokens * settings.ai_cost_per_token,
            status="success" if result.success else "failed",
            error_message=result.error, retry_count=result.retry_count,
            duration_ms=result.duration_ms,
        )

        if not result.success:
            logger.error(f"PRD generation failed: {result.error}")
            return 0

        parsed = AIOutputValidator.parse_and_validate(result.text, PRDOutput)
        if not parsed:
            logger.error("PRD output validation failed")
            return 0

        total = 0
        for v in parsed.versions:
            version = PRDVersion(
                session_id=session_id,
                version_no=v.version,
                name=v.name,
                priority=total,
            )
            db.add(version)
            db.flush()

            for req in v.requirements:
                requirement = PRDRequirement(
                    session_id=session_id,
                    version_id=version.id,
                    req_id=req.req_id,
                    title=req.title,
                    description=req.description,
                    priority=req.priority,
                    source_finding_ids=json.dumps(req.source_finding_ids),
                )
                db.add(requirement)
                total += 1

        db.commit()
        return total


prd_generator = PRDGenerator()
