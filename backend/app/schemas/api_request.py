from pydantic import BaseModel
from typing import Optional


class StartWorkflowRequest(BaseModel):
    app_url: str
    user_goal: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    session_id: str
    status: str
    current_step: int
    total_steps: int = 9


class SessionResponse(BaseModel):
    id: str
    app_id: str
    app_name: Optional[str]
    app_url: str
    user_goal: Optional[str]
    status: str
    current_step: int
    total_tokens: int
    total_cost: float
    ai_call_count: int
    ai_fail_count: int
    ai_retry_count: int
    duration_seconds: int
    error_message: Optional[str]
    created_at: Optional[str]
