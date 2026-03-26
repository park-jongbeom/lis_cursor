"""Agent query DTOs."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel


class AgentQueryRequest(BaseModel):
    session_id: uuid.UUID | None = None
    query: str
    dataset_id: uuid.UUID | None = None
    language: str = "ko"


class AgentQueryResponse(BaseModel):
    session_id: uuid.UUID
    query: str
    answer: str
    supporting_data: dict[str, Any] | None = None
    route_used: str  # "pandas_tier1" | "ai_tier2"
    llm_model: str | None = None
    processing_time_ms: int | None = None
