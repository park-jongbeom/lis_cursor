"""Hybrid Tier 1 / Tier 2 complexity scoring."""

from __future__ import annotations

from enum import IntEnum, StrEnum

from pydantic import BaseModel, Field

from app.core.config import settings


class QueryType(IntEnum):
    AGGREGATION = 10
    FORECAST = 30
    CLUSTER = 35
    TREND = 25
    NATURAL_LANGUAGE = 80
    ANOMALY_EXPLAIN = 75


class Route(StrEnum):
    PANDAS = "pandas"
    AI = "ai"


class ComplexityScore(BaseModel):
    score: int
    route: Route


class RoutingRequest(BaseModel):
    """입력 DTO for ComplexityScorer (엔드포인트/서비스에서 채워 전달)."""

    query_type: QueryType
    row_count: int = Field(default=0, ge=0)
    cross_table: bool = False


class ComplexityScorer:
    WEIGHTS: dict[QueryType, int] = {
        QueryType.AGGREGATION: 10,
        QueryType.FORECAST: 30,
        QueryType.CLUSTER: 35,
        QueryType.TREND: 25,
        QueryType.NATURAL_LANGUAGE: 80,
        QueryType.ANOMALY_EXPLAIN: 75,
    }

    @classmethod
    def score(cls, request: RoutingRequest) -> ComplexityScore:
        base = cls.WEIGHTS[request.query_type]
        if request.row_count >= 1_000_000:
            size_penalty = 20
        elif request.row_count >= 500_000:
            size_penalty = 10
        else:
            size_penalty = 0
        cross_bonus = 15 if request.cross_table else 0
        total = base + size_penalty + cross_bonus
        route = Route.AI if total >= settings.AI_ESCALATION_THRESHOLD else Route.PANDAS
        return ComplexityScore(score=total, route=route)
