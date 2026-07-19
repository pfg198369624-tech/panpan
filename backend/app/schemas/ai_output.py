from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from decimal import Decimal, InvalidOperation


class ClassificationOutput(BaseModel):
    review_index: int = Field(ge=0)
    topic: str = Field(min_length=1)
    subtopic: Optional[str] = None
    sentiment: str = Field(default="neutral")
    confidence: float = Field(default=0.5, ge=0, le=1)

    @field_validator("review_index", mode="before")
    @classmethod
    def coerce_review_index(cls, v: Any) -> int:
        if isinstance(v, str):
            try:
                return int(v.strip())
            except (ValueError, TypeError):
                return 0
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def coerce_confidence(cls, v: Any) -> float:
        if isinstance(v, str):
            v = v.strip().rstrip("%")
            try:
                return float(Decimal(v))
            except (InvalidOperation, ValueError, TypeError):
                return 0.5
        return v


class FindingOutput(BaseModel):
    evidence_sufficient: bool
    conflicting_feedback: Optional[str] = None
    confidence: str = Field(pattern="^(high|medium|low|uncertain)$")
    data_limitations: Optional[str] = None
    recommendation: Optional[str] = None


class PRDRequirementOutput(BaseModel):
    req_id: str
    title: str = Field(min_length=1)
    description: str
    priority: str = Field(pattern="^(P0|P1|P2)$")
    source_finding_ids: List[int] = Field(min_length=1)
    source_review_excerpts: List[str]


class PRDVersionOutput(BaseModel):
    version: str
    name: str
    requirements: List[PRDRequirementOutput]


class PRDOutput(BaseModel):
    versions: List[PRDVersionOutput]


class TestCaseOutput(BaseModel):
    case_id: str
    title: str
    preconditions: str
    steps: List[str] = Field(min_length=1)
    expected_result: str
    source_review_ids: List[int]


class TestCaseListOutput(BaseModel):
    test_cases: List[TestCaseOutput]


class ScopeOutput(BaseModel):
    scope_description: str
    target_versions: Optional[List[str]] = None
    rating_focus: Optional[str] = None
    data_requirements: Optional[str] = None


class EvidenceEvalOutput(BaseModel):
    evidence_sufficient: bool
    conflicting_feedback: Optional[str] = None
    confidence: str = Field(pattern="^(high|medium|low|uncertain)$")
    data_limitations: Optional[str] = None
    recommendation: Optional[str] = None


class ValidationIssue(BaseModel):
    type: str
    entity_id: str
    description: str
    suggestion: Optional[str] = None


class ValidationReport(BaseModel):
    passed: bool
    issues: List[ValidationIssue] = []
    revisions: List[str] = []


class AnalysisFindingItem(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    source_review_indices: List[int] = []
    confidence: str = "medium"
    conflicting_evidence: Optional[str] = None
    data_limitations: Optional[str] = None
    recommendation: Optional[str] = None

    @field_validator("source_review_indices", mode="before")
    @classmethod
    def coerce_indices(cls, v: Any) -> List[int]:
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, str):
                    try:
                        result.append(int(item.strip()))
                    except (ValueError, TypeError):
                        continue
                else:
                    result.append(item)
            return result
        return v


class SinglePassOutput(BaseModel):
    classifications: List[ClassificationOutput] = []
    findings: List[AnalysisFindingItem] = []
