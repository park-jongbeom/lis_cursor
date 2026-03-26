"""CRM clustering and churn DTOs."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class ClusterRequest(BaseModel):
    dataset_id: uuid.UUID
    n_clusters: int = 4


class ClusterResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    cluster_count: int
    processing_time_ms: int | None = None


class ChurnRiskItem(BaseModel):
    customer_code: str
    customer_name: str
    last_order_days_ago: int
    churn_risk_score: float  # 0.0 ~ 1.0
    rfm_segment: str  # "at_risk" | "champions" | "loyal" | "lost"
    recommended_action: str


class ChurnRiskResponse(BaseModel):
    analysis_date: str  # "2026-03-26"
    high_risk_customers: list[ChurnRiskItem]
    total_at_risk: int
    processing_time_ms: int | None = None


class ChurnRiskCompactCustomer(BaseModel):
    code: str
    name: str
    risk_score: float


class ChurnRiskCompactResponse(BaseModel):
    high_risk_count: int
    top_customers: list[ChurnRiskCompactCustomer]
    cluster_count: int
    summary: str
