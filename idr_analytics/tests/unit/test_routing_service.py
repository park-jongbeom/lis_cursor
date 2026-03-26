"""AnalysisRoutingService 단위 테스트 — 서비스 mock."""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
from app.core.routing import ComplexityScore, QueryType, Route, RoutingRequest
from app.services.analytics.routing_service import (
    BIRegionalTrendContext,
    BITopTestsContext,
    CRMClusterContext,
    SCMForecastContext,
    routing_service,
)


def _make_db() -> AsyncMock:
    return AsyncMock()


def _pandas_score() -> ComplexityScore:
    return ComplexityScore(score=10, route=Route.PANDAS)


def _ai_score() -> ComplexityScore:
    return ComplexityScore(score=80, route=Route.AI)


# ── Pandas 분기 ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_route_forecast_pandas() -> None:
    """RT-01: FORECAST + Pandas 경로 → scm_service.forecast 호출."""
    df = pd.DataFrame({"order_date": ["2026-01-01"], "test_code": ["X"], "qty": [10.0]})
    ctx = SCMForecastContext(df=df, target_col="qty", date_col="order_date", group_col="test_code", periods=3)
    request = RoutingRequest(query_type=QueryType.FORECAST, row_count=100)

    mock_forecasts = [MagicMock()]
    with patch("app.services.analytics.routing_service.ComplexityScorer.score", return_value=_pandas_score()):
        with patch("app.services.analytics.routing_service.scm_service") as mock_scm:
            mock_scm.forecast = AsyncMock(return_value=mock_forecasts)
            result = await routing_service.route(request, _make_db(), pandas_context=ctx)

    assert result.pandas_result is mock_forecasts
    assert result.agent_response is None
    mock_scm.forecast.assert_awaited_once()


@pytest.mark.asyncio
async def test_route_cluster_pandas() -> None:
    """RT-02: CLUSTER + Pandas 경로 → crm cluster 진입."""
    df = pd.DataFrame(
        {
            "customer_code": ["C001", "C002", "C003", "C004", "C005"],
            "order_date": ["2026-01-01"] * 5,
            "order_amount": [100.0, 200.0, 300.0, 400.0, 500.0],
        }
    )
    ctx = CRMClusterContext(df=df, reference_date=date(2026, 3, 26), n_clusters=2)
    request = RoutingRequest(query_type=QueryType.CLUSTER, row_count=5)

    with patch("app.services.analytics.routing_service.ComplexityScorer.score", return_value=_pandas_score()):
        result = await routing_service.route(request, _make_db(), pandas_context=ctx)

    assert result.pandas_result is not None
    assert result.agent_response is None


@pytest.mark.asyncio
async def test_route_trend_pandas() -> None:
    """RT-03: TREND + Pandas 경로 → bi_service.regional_trend 호출."""
    df = pd.DataFrame({"period": ["2026Q1"], "region": ["서울"], "value": [100.0]})
    ctx = BIRegionalTrendContext(df=df, period_col="period", region_col="region", value_col="value")
    request = RoutingRequest(query_type=QueryType.TREND, row_count=1)

    with patch("app.services.analytics.routing_service.ComplexityScorer.score", return_value=_pandas_score()):
        with patch("app.services.analytics.routing_service.bi_service") as mock_bi:
            mock_bi.regional_trend.return_value = df
            result = await routing_service.route(request, _make_db(), pandas_context=ctx)

    assert result.pandas_result is not None
    mock_bi.regional_trend.assert_called_once()


@pytest.mark.asyncio
async def test_route_aggregation_pandas() -> None:
    """RT-04: AGGREGATION + Pandas 경로 → bi_service.top_tests 호출."""
    df = pd.DataFrame({"period": ["202601"], "test_code": ["BRCA1"], "value": [100.0]})
    ctx = BITopTestsContext(df=df, period="202601", top_n=5)
    request = RoutingRequest(query_type=QueryType.AGGREGATION, row_count=1)

    with patch("app.services.analytics.routing_service.ComplexityScorer.score", return_value=_pandas_score()):
        with patch("app.services.analytics.routing_service.bi_service") as mock_bi:
            mock_bi.top_tests.return_value = df
            result = await routing_service.route(request, _make_db(), pandas_context=ctx)

    assert result.pandas_result is not None
    mock_bi.top_tests.assert_called_once()


# ── AI 분기 ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_route_ai_path() -> None:
    """RT-05: score ≥ 70 → agent_service.analyze 호출, agent_response 존재."""
    request = RoutingRequest(query_type=QueryType.NATURAL_LANGUAGE, row_count=0)
    mock_agent_response = MagicMock()

    with patch("app.services.analytics.routing_service.ComplexityScorer.score", return_value=_ai_score()):
        with patch("app.services.analytics.routing_service.agent_service") as mock_agent:
            mock_agent.analyze = AsyncMock(return_value=mock_agent_response)
            result = await routing_service.route(
                request, _make_db(), nl_query="이탈 고객 분석", dataset_id=uuid.uuid4()
            )

    assert result.agent_response is mock_agent_response
    assert result.pandas_result is None
    mock_agent.analyze.assert_awaited_once()


# ── 오류 케이스 ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_route_forecast_missing_context_raises() -> None:
    """RT-06: FORECAST + context 없음 → ValueError."""
    request = RoutingRequest(query_type=QueryType.FORECAST, row_count=100)

    with patch("app.services.analytics.routing_service.ComplexityScorer.score", return_value=_pandas_score()):
        with pytest.raises(ValueError, match="SCMForecastContext"):
            await routing_service.route(request, _make_db(), pandas_context=None)


def test_complexity_score_boundary() -> None:
    """RT-07: score=70 → Route.AI (경계값)."""
    score = ComplexityScore(score=70, route=Route.AI)
    assert score.route == Route.AI
