"""SCM forecast request/response DTOs."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class ForecastRequest(BaseModel):
    dataset_id: uuid.UUID
    target_column: str
    date_column: str
    group_by: str
    test_codes: list[str]
    forecast_days: int = 30
    model: str = "prophet"  # "prophet" | "arima"


class PredictionPoint(BaseModel):
    ds: str  # "2026-04-01"
    yhat: float
    yhat_lower: float
    yhat_upper: float


class ForecastItem(BaseModel):
    test_code: str
    predictions: list[PredictionPoint]
    trend_direction: str  # "increasing" | "decreasing" | "stable"
    seasonality: dict[str, bool]  # {"weekly": true, "yearly": true}


class ForecastResponse(BaseModel):
    job_id: uuid.UUID
    status: str  # "pending" | "running" | "completed" | "failed"
    model_used: str
    forecasts: list[ForecastItem]
    processing_time_ms: int | None = None


class ForecastCompactItem(BaseModel):
    test_code: str
    predicted_qty: float
    trend: str


class ForecastCompactResponse(BaseModel):
    forecast_period_days: int
    high_demand_items: list[ForecastCompactItem]
    restock_alerts: int
    summary: str
