"""Analytics services."""

from __future__ import annotations

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

__all__ = [
    "AnalysisRoutingService",
    "BIService",
    "BIRegionalTrendContext",
    "BITopTestsContext",
    "CRMClusterContext",
    "CRMService",
    "PandasContext",
    "RoutingExecutionResult",
    "SCMForecastContext",
    "SCMService",
    "bi_service",
    "crm_service",
    "routing_service",
    "scm_service",
]
