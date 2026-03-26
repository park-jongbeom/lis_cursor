"""ARQ worker job unit tests."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest
from app.workers.arq_worker import cluster_job, forecast_job, trend_job


class _DummySessionCtx:
    async def __aenter__(self) -> object:
        return object()

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class _ForecastItem:
    def __init__(self, code: str) -> None:
        self.code = code

    def model_dump(self) -> dict[str, object]:
        return {"test_code": self.code, "predictions": []}


@pytest.mark.asyncio
async def test_forecast_job_success() -> None:
    dataset_id = str(uuid.uuid4())
    payload = {
        "target_column": "order_qty",
        "date_column": "order_date",
        "group_by": "test_code",
        "forecast_days": 7,
        "test_codes": ["T1"],
    }
    df = pd.DataFrame(
        {
            "order_date": ["2026-01-01", "2026-01-02"],
            "test_code": ["T1", "T1"],
            "order_qty": [10, 12],
        }
    )
    row = SimpleNamespace(file_path="/tmp/fake.csv")

    with (
        patch("app.workers.arq_worker.async_session_factory", return_value=_DummySessionCtx()),
        patch("app.workers.arq_worker.dataset_crud.get", new=AsyncMock(return_value=row)),
        patch("app.workers.arq_worker.ingestion_service.read_csv_validated", return_value=(df, 2)),
        patch(
            "app.workers.arq_worker.scm_service.forecast",
            new=AsyncMock(return_value=[_ForecastItem("T1")]),
        ),
    ):
        result = await forecast_job({}, dataset_id, payload)

    assert result["model_used"] == "prophet_or_arima"
    assert isinstance(result["forecasts"], list)
    assert result["forecasts"][0]["test_code"] == "T1"
    assert isinstance(result["processing_time_ms"], int)


@pytest.mark.asyncio
async def test_cluster_job_dataset_not_found() -> None:
    dataset_id = str(uuid.uuid4())

    with (
        patch("app.workers.arq_worker.async_session_factory", return_value=_DummySessionCtx()),
        patch("app.workers.arq_worker.dataset_crud.get", new=AsyncMock(return_value=None)),
    ):
        with pytest.raises(ValueError, match="not found"):
            await cluster_job({}, dataset_id, 4)


@pytest.mark.asyncio
async def test_cluster_job_success() -> None:
    dataset_id = str(uuid.uuid4())
    source_df = pd.DataFrame(
        {
            "customer_code": ["C1", "C2"],
            "order_date": ["2026-01-01", "2026-01-02"],
            "order_amount": [100.0, 200.0],
        }
    )
    clustered = pd.DataFrame(
        {
            "customer_code": ["C1", "C2"],
            "recency_days": [120, 3],
            "rfm_segment": ["at_risk", "champions"],
        }
    )
    row = SimpleNamespace(file_path="/tmp/fake.csv")

    with (
        patch("app.workers.arq_worker.async_session_factory", return_value=_DummySessionCtx()),
        patch("app.workers.arq_worker.dataset_crud.get", new=AsyncMock(return_value=row)),
        patch(
            "app.workers.arq_worker.ingestion_service.read_csv_validated",
            return_value=(source_df, 2),
        ),
        patch("app.workers.arq_worker.crm_service.build_rfm_features", return_value=source_df),
        patch("app.workers.arq_worker.crm_service.cluster", return_value=clustered),
    ):
        result = await cluster_job({}, dataset_id, 2)

    assert result["cluster_count"] == 2
    assert result["customer_total"] == 2
    assert len(result["sample"]) == 2
    assert result["sample"][0]["customer_code"] == "C1"


@pytest.mark.asyncio
async def test_trend_job_success() -> None:
    dataset_id = str(uuid.uuid4())
    source_df = pd.DataFrame({"period": ["2026-Q1"], "region": ["SEOUL"], "value": [10]})
    trend_df = pd.DataFrame([{"period": "2026-Q1", "region": "SEOUL", "order_count": 10, "yoy_growth": 0.1}])
    row = SimpleNamespace(file_path="/tmp/fake.csv")

    with (
        patch("app.workers.arq_worker.async_session_factory", return_value=_DummySessionCtx()),
        patch("app.workers.arq_worker.dataset_crud.get", new=AsyncMock(return_value=row)),
        patch(
            "app.workers.arq_worker.ingestion_service.read_csv_validated",
            return_value=(source_df, 1),
        ),
        patch("app.workers.arq_worker.bi_service.regional_trend", return_value=trend_df),
    ):
        result = await trend_job({}, dataset_id, "period", "region", "value")

    assert isinstance(result["rows"], list)
    assert result["rows"][0]["region"] == "SEOUL"
    assert isinstance(result["processing_time_ms"], int)
