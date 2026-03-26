"""BI trend and heatmap DTOs."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class TrendRequest(BaseModel):
    dataset_id: uuid.UUID
    period_col: str
    region_col: str
    value_col: str


class TrendResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    processing_time_ms: int | None = None


class HeatmapEntry(BaseModel):
    region: str
    order_count: int
    yoy_growth: float  # 0.14 = 14% 증가
    top_test: str


class HeatmapResponse(BaseModel):
    period: str  # "202603"
    test_category: str
    heatmap: list[HeatmapEntry]
    insight: str | None = None


class HeatmapHighlight(BaseModel):
    region: str
    test: str
    growth_rate: float


class HeatmapCompactResponse(BaseModel):
    period: str
    top_regions: list[str]
    trending_tests: list[str]
    heatmap_highlights: list[HeatmapHighlight]
    summary: str
