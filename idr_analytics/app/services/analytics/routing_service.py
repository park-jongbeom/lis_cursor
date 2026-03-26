"""Complexity 기반 Pandas vs Dify 분기 및 서비스 오케스트레이션."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.routing import ComplexityScore, ComplexityScorer, QueryType, Route, RoutingRequest
from app.schemas.agent import AgentQueryResponse
from app.services.ai.agent_service import agent_service
from app.services.analytics.bi_service import bi_service
from app.services.analytics.crm_service import crm_service
from app.services.analytics.scm_service import scm_service


@dataclass
class SCMForecastContext:
    df: pd.DataFrame
    target_col: str
    date_col: str
    group_col: str
    periods: int = 30


@dataclass
class CRMClusterContext:
    df: pd.DataFrame
    reference_date: date | datetime
    n_clusters: int = 4


@dataclass
class BIRegionalTrendContext:
    df: pd.DataFrame
    period_col: str
    region_col: str
    value_col: str


@dataclass
class BITopTestsContext:
    df: pd.DataFrame
    period: str
    top_n: int
    period_col: str = "period"
    test_col: str = "test_code"
    value_col: str = "value"


PandasContext = SCMForecastContext | CRMClusterContext | BIRegionalTrendContext | BITopTestsContext | None


@dataclass
class RoutingExecutionResult:
    complexity: ComplexityScore
    pandas_result: Any | None = None
    agent_response: AgentQueryResponse | None = None


def _run_crm_cluster(ctx: CRMClusterContext) -> pd.DataFrame:
    rfm = crm_service.build_rfm_features(ctx.df, ctx.reference_date)
    return crm_service.cluster(rfm, n_clusters=ctx.n_clusters)


class AnalysisRoutingService:
    async def route(
        self,
        request: RoutingRequest,
        db: AsyncSession,
        *,
        pandas_context: PandasContext = None,
        nl_query: str = "",
        dataset_id: uuid.UUID | None = None,
        session_id: uuid.UUID | None = None,
        ai_inputs: dict[str, str] | None = None,
    ) -> RoutingExecutionResult:
        _ = db  # Phase 5에서 churn 등 DB 연동 시 사용
        score = ComplexityScorer.score(request)
        if score.route == Route.AI:
            agent = await agent_service.analyze(nl_query, dataset_id, session_id, extra_inputs=ai_inputs)
            return RoutingExecutionResult(complexity=score, agent_response=agent, pandas_result=None)

        if request.query_type == QueryType.FORECAST:
            if not isinstance(pandas_context, SCMForecastContext):
                msg = "SCMForecastContext required for FORECAST pandas path"
                raise ValueError(msg)
            forecasts = await scm_service.forecast(
                pandas_context.df,
                pandas_context.target_col,
                pandas_context.date_col,
                pandas_context.group_col,
                pandas_context.periods,
            )
            return RoutingExecutionResult(complexity=score, pandas_result=forecasts, agent_response=None)

        if request.query_type == QueryType.CLUSTER:
            if not isinstance(pandas_context, CRMClusterContext):
                msg = "CRMClusterContext required for CLUSTER pandas path"
                raise ValueError(msg)
            clustered = await asyncio.to_thread(_run_crm_cluster, pandas_context)
            return RoutingExecutionResult(complexity=score, pandas_result=clustered, agent_response=None)

        if request.query_type == QueryType.TREND:
            if not isinstance(pandas_context, BIRegionalTrendContext):
                msg = "BIRegionalTrendContext required for TREND pandas path"
                raise ValueError(msg)
            trend_df = await asyncio.to_thread(
                bi_service.regional_trend,
                pandas_context.df,
                pandas_context.period_col,
                pandas_context.region_col,
                pandas_context.value_col,
            )
            return RoutingExecutionResult(complexity=score, pandas_result=trend_df, agent_response=None)

        if request.query_type == QueryType.AGGREGATION:
            if not isinstance(pandas_context, BITopTestsContext):
                msg = "BITopTestsContext required for AGGREGATION pandas path"
                raise ValueError(msg)
            top_df = await asyncio.to_thread(
                lambda: bi_service.top_tests(
                    pandas_context.df,
                    pandas_context.period,
                    pandas_context.top_n,
                    period_col=pandas_context.period_col,
                    test_col=pandas_context.test_col,
                    value_col=pandas_context.value_col,
                )
            )
            return RoutingExecutionResult(complexity=score, pandas_result=top_df, agent_response=None)

        msg = f"No pandas path implemented for query_type={request.query_type!r}"
        raise ValueError(msg)


routing_service = AnalysisRoutingService()
