"""Phase 3 Pydantic 스키마 단위 테스트."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from app.schemas.agent import AgentQueryRequest, AgentQueryResponse
from app.schemas.bi import (
    HeatmapCompactResponse,
    HeatmapEntry,
    HeatmapHighlight,
    HeatmapResponse,
    TrendRequest,
)
from app.schemas.crm import (
    ChurnRiskCompactCustomer,
    ChurnRiskCompactResponse,
    ChurnRiskItem,
    ChurnRiskResponse,
    ClusterRequest,
)
from app.schemas.dataset import DatasetProfileResponse, DatasetUploadRequest
from app.schemas.scm import (
    ForecastCompactItem,
    ForecastCompactResponse,
    ForecastItem,
    ForecastRequest,
    PredictionPoint,
)
from pydantic import ValidationError


def test_dataset_upload_request_valid() -> None:
    r = DatasetUploadRequest(dataset_name="scm_q1", dataset_type="scm")
    assert r.dataset_name == "scm_q1"
    assert r.dataset_type == "scm"


def test_dataset_upload_request_missing_fields() -> None:
    with pytest.raises(ValidationError):
        DatasetUploadRequest(dataset_name="only_name")  # type: ignore[call-arg]


def test_dataset_profile_response_from_alias() -> None:
    ds_id = uuid.uuid4()
    created = datetime(2026, 3, 26, 12, 0, 0)
    r = DatasetProfileResponse.model_validate(
        {
            "id": ds_id,
            "name": "profile_ds",
            "row_count": 100,
            "created_at": created,
        }
    )
    assert r.dataset_id == ds_id
    assert r.dataset_name == "profile_ds"


def test_dataset_profile_response_defaults() -> None:
    ds_id = uuid.uuid4()
    created = datetime(2026, 3, 26, 12, 0, 0)
    r = DatasetProfileResponse.model_validate(
        {
            "id": ds_id,
            "name": "x",
            "row_count": 0,
            "created_at": created,
        }
    )
    assert r.columns == []
    assert r.dtypes == {}
    assert r.null_counts == {}


def test_forecast_request_defaults() -> None:
    fid = uuid.uuid4()
    r = ForecastRequest(
        dataset_id=fid,
        target_column="qty",
        date_column="ds",
        group_by="test_code",
        test_codes=["T1"],
    )
    assert r.forecast_days == 30
    assert r.model == "prophet"


def test_forecast_compact_response_valid() -> None:
    r = ForecastCompactResponse(
        forecast_period_days=30,
        high_demand_items=[
            ForecastCompactItem(test_code="A", predicted_qty=12.5, trend="up"),
        ],
        restock_alerts=2,
        summary="ok",
    )
    assert r.restock_alerts == 2
    assert len(r.high_demand_items) == 1


def test_prediction_point_valid() -> None:
    p = PredictionPoint(ds="2026-04-01", yhat=1.0, yhat_lower=0.5, yhat_upper=1.5)
    assert p.ds == "2026-04-01"
    assert p.yhat == pytest.approx(1.0)


def test_forecast_item_seasonality_dict() -> None:
    item = ForecastItem(
        test_code="X",
        predictions=[
            PredictionPoint(ds="2026-01-01", yhat=1.0, yhat_lower=0.0, yhat_upper=2.0),
        ],
        trend_direction="stable",
        seasonality={"weekly": True, "yearly": False},
    )
    assert item.seasonality["weekly"] is True


def test_cluster_request_defaults() -> None:
    r = ClusterRequest(dataset_id=uuid.uuid4())
    assert r.n_clusters == 4


def test_churn_risk_item_score_range() -> None:
    item = ChurnRiskItem(
        customer_code="C1",
        customer_name="Acme",
        last_order_days_ago=120,
        churn_risk_score=0.85,
        rfm_segment="at_risk",
        recommended_action="call",
    )
    assert 0.0 <= item.churn_risk_score <= 1.0


def test_churn_risk_compact_response_valid() -> None:
    r = ChurnRiskCompactResponse(
        high_risk_count=3,
        top_customers=[
            ChurnRiskCompactCustomer(code="C1", name="A", risk_score=0.9),
        ],
        cluster_count=4,
        summary="compact",
    )
    assert r.high_risk_count == 3
    assert len(r.top_customers) == 1


def test_churn_risk_response_none_processing_time() -> None:
    r = ChurnRiskResponse(
        analysis_date="2026-03-26",
        high_risk_customers=[],
        total_at_risk=0,
        processing_time_ms=None,
    )
    assert r.processing_time_ms is None


def test_trend_request_valid() -> None:
    r = TrendRequest(
        dataset_id=uuid.uuid4(),
        period_col="ym",
        region_col="region",
        value_col="amount",
    )
    assert r.period_col == "ym"


def test_heatmap_entry_growth_float() -> None:
    e = HeatmapEntry(region="KR", order_count=10, yoy_growth=0.14, top_test="CBC")
    assert e.yoy_growth == pytest.approx(0.14)


def test_heatmap_compact_response_list_fields() -> None:
    r = HeatmapCompactResponse(
        period="202603",
        top_regions=["A", "B"],
        trending_tests=["T1", "T2"],
        heatmap_highlights=[
            HeatmapHighlight(region="A", test="T1", growth_rate=0.2),
        ],
        summary="s",
    )
    assert r.top_regions == ["A", "B"]
    assert r.trending_tests == ["T1", "T2"]


def test_heatmap_response_insight_none() -> None:
    r = HeatmapResponse(
        period="202603",
        test_category="blood",
        heatmap=[],
        insight=None,
    )
    assert r.insight is None


def test_agent_query_request_defaults() -> None:
    r = AgentQueryRequest(query="hello")
    assert r.session_id is None
    assert r.dataset_id is None
    assert r.language == "ko"


def test_agent_query_request_language_override() -> None:
    r = AgentQueryRequest(query="hi", language="en")
    assert r.language == "en"


def test_agent_query_response_valid() -> None:
    sid = uuid.uuid4()
    r_none = AgentQueryResponse(
        session_id=sid,
        query="q",
        answer="a",
        supporting_data=None,
        route_used="pandas_tier1",
        llm_model=None,
        processing_time_ms=None,
    )
    assert r_none.supporting_data is None
    r_dict = AgentQueryResponse(
        session_id=sid,
        query="q",
        answer="a",
        supporting_data={"customers_analyzed": 3},
        route_used="ai_tier2",
        llm_model="claude",
        processing_time_ms=100,
    )
    assert r_dict.supporting_data == {"customers_analyzed": 3}


def test_agent_query_response_route_used() -> None:
    r = AgentQueryResponse(
        session_id=uuid.uuid4(),
        query="x",
        answer="y",
        route_used="custom_route_label",
    )
    assert r.route_used == "custom_route_label"
