"""Application services."""

from __future__ import annotations

from app.services.ai.agent_service import AgentService, agent_service
from app.services.analytics.bi_service import BIService, bi_service
from app.services.analytics.crm_service import CRMService, crm_service
from app.services.analytics.routing_service import (
    AnalysisRoutingService,
    BIRegionalTrendContext,
    BITopTestsContext,
    CRMClusterContext,
    PandasContext,
    RoutingExecutionResult,
    SCMForecastContext,
    routing_service,
)
from app.services.analytics.scm_service import SCMService, scm_service
from app.services.data.ingestion_service import IngestionService, ingestion_service
from app.services.data.preprocessing_service import PreprocessingService, preprocessing_service

__all__ = [
    "AgentService",
    "AnalysisRoutingService",
    "BIService",
    "BIRegionalTrendContext",
    "BITopTestsContext",
    "CRMClusterContext",
    "CRMService",
    "IngestionService",
    "PandasContext",
    "PreprocessingService",
    "RoutingExecutionResult",
    "SCMForecastContext",
    "SCMService",
    "agent_service",
    "bi_service",
    "crm_service",
    "ingestion_service",
    "preprocessing_service",
    "routing_service",
    "scm_service",
]
