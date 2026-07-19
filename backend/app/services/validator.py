import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.services.ai_client import ai_client
from app.core.prompt_manager import prompt_manager
from app.schemas.validator import AIOutputValidator
from app.models.finding import Finding
from app.models.prd import PRDRequirement
from app.models.test_case import TestCase

logger = logging.getLogger(__name__)


class Validator:
    def validate_traceability(self, db: Session, session_id: str) -> dict:
        findings = db.query(Finding).filter(Finding.session_id == session_id).all()
        requirements = db.query(PRDRequirement).filter(PRDRequirement.session_id == session_id).all()
        test_cases = db.query(TestCase).filter(TestCase.session_id == session_id).all()

        issues = []
        revisions = []

        for f in findings:
            ids = f.source_review_ids
            if isinstance(ids, str):
                try:
                    ids = json.loads(ids)
                except Exception:
                    ids = []
            if not ids or len(ids) == 0:
                f.conclusion_type = "assumption"
                issues.append({
                    "type": "missing_traceability",
                    "entity_id": f"finding_{f.id}",
                    "description": f"Finding '{f.title}' has no source review IDs",
                })

        for r in requirements:
            ids = r.source_finding_ids
            if isinstance(ids, str):
                try:
                    ids = json.loads(ids)
                except Exception:
                    ids = []
            if not ids or len(ids) == 0:
                issues.append({
                    "type": "missing_traceability",
                    "entity_id": r.req_id,
                    "description": f"Requirement {r.req_id} has no source finding IDs",
                })
                revisions.append(f"REQ-{r.req_id}: marked as assumption - no source findings")

        for t in test_cases:
            ids = t.source_review_ids
            if isinstance(ids, str):
                try:
                    ids = json.loads(ids)
                except Exception:
                    ids = []
            if not ids or len(ids) == 0:
                issues.append({
                    "type": "missing_traceability",
                    "entity_id": t.case_id,
                    "description": f"Test case {t.case_id} has no source review IDs",
                })

        db.commit()

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "revisions": revisions,
            "summary": {
                "total_findings": len(findings),
                "total_requirements": len(requirements),
                "total_test_cases": len(test_cases),
                "total_issues": len(issues),
            },
        }


validator = Validator()
