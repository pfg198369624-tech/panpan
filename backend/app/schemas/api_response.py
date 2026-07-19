from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime


class ApiResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
