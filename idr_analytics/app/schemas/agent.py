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
    # QueryType 정수값(10~80). 생략 시 자연어(80)로 간주
    query_type: int | None = None
    # Tier 1(Pandas) 분기용 선택 컬럼·파라미터
    target_column: str | None = None
    date_column: str | None = None
    group_by_column: str | None = None
    forecast_days: int = 30
    n_clusters: int = 4
    period_column: str | None = None
    region_column: str | None = None
    value_column: str | None = None
    aggregation_period: str | None = None
    top_n: int = 10
    test_column: str | None = None


class AgentQueryResponse(BaseModel):
    session_id: uuid.UUID
    query: str
    answer: str
    supporting_data: dict[str, Any] | None = None
    route_used: str  # "pandas_tier1" | "ai_tier2"
    llm_model: str | None = None
    processing_time_ms: int | None = None
