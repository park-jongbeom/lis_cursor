"""Pydantic DTOs for API and services."""

from app.schemas.agent import AgentQueryRequest, AgentQueryResponse
from app.schemas.bi import (
    HeatmapCompactResponse,
    HeatmapEntry,
    HeatmapHighlight,
    HeatmapResponse,
    TrendRequest,
    TrendResponse,
)
from app.schemas.crm import (
    ChurnRiskCompactCustomer,
    ChurnRiskCompactResponse,
    ChurnRiskItem,
    ChurnRiskResponse,
    ClusterRequest,
    ClusterResponse,
)
from app.schemas.dataset import DatasetProfileResponse, DatasetUploadRequest
from app.schemas.scm import (
    ForecastCompactItem,
    ForecastCompactResponse,
    ForecastItem,
    ForecastRequest,
    ForecastResponse,
    PredictionPoint,
)

__all__ = [
    "AgentQueryRequest",
    "AgentQueryResponse",
    "ChurnRiskCompactCustomer",
    "ChurnRiskCompactResponse",
    "ChurnRiskItem",
    "ChurnRiskResponse",
    "ClusterRequest",
    "ClusterResponse",
    "DatasetProfileResponse",
    "DatasetUploadRequest",
    "ForecastCompactItem",
    "ForecastCompactResponse",
    "ForecastItem",
    "ForecastRequest",
    "ForecastResponse",
    "HeatmapCompactResponse",
    "HeatmapEntry",
    "HeatmapHighlight",
    "HeatmapResponse",
    "PredictionPoint",
    "TrendRequest",
    "TrendResponse",
]
