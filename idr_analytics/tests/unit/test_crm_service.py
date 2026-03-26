"""CRMService 단위 테스트."""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
from app.services.analytics.crm_service import (
    build_rfm_features,
    cluster,
    crm_service,
)

# ── 픽스처 ─────────────────────────────────────────────────────────────────────


@pytest.fixture()
def crm_df() -> pd.DataFrame:
    """5명 고객, 기준일 기준 recency 다양."""
    return pd.DataFrame(
        {
            "customer_code": ["C001", "C002", "C003", "C004", "C005"],
            "customer_name": ["병원A", "병원B", "병원C", "병원D", "병원E"],
            "order_date": [
                "2025-01-01",  # 오래됨 → 고위험
                "2025-06-01",
                "2025-12-01",
                "2026-01-01",
                "2026-02-01",
            ],
            "order_amount": [100.0, 200.0, 300.0, 400.0, 500.0],
        }
    )


_REF = datetime(2026, 3, 26)


# ── build_rfm_features ─────────────────────────────────────────────────────────


def test_rfm_columns_exist(crm_df: pd.DataFrame) -> None:
    """R-01: recency_days, R_score, F_score, M_score 컬럼 존재."""
    out = build_rfm_features(crm_df, _REF)
    for col in ("recency_days", "R_score", "F_score", "M_score"):
        assert col in out.columns, f"Missing column: {col}"


def test_rfm_score_range(crm_df: pd.DataFrame) -> None:
    """R-02: 점수 범위 1 ≤ score ≤ 5."""
    out = build_rfm_features(crm_df, _REF)
    for col in ("R_score", "F_score", "M_score"):
        assert out[col].min() >= 1
        assert out[col].max() <= 5


def test_rfm_missing_required_column_raises() -> None:
    """R-03: 필수 컬럼 누락 → KeyError."""
    df = pd.DataFrame({"customer_code": ["C001"], "order_date": ["2026-01-01"]})
    with pytest.raises(KeyError, match="order_amount"):
        build_rfm_features(df, _REF)


def test_rfm_original_unchanged(crm_df: pd.DataFrame) -> None:
    """R-04: 원본 불변."""
    original_cols = set(crm_df.columns)
    build_rfm_features(crm_df, _REF)
    assert set(crm_df.columns) == original_cols


def test_rfm_customer_name_merged(crm_df: pd.DataFrame) -> None:
    """R-01b: customer_name 컬럼 있으면 merge 후 포함."""
    out = build_rfm_features(crm_df, _REF)
    assert "customer_name" in out.columns


def test_rfm_recency_days_positive(crm_df: pd.DataFrame) -> None:
    """R-01c: recency_days >= 0."""
    out = build_rfm_features(crm_df, _REF)
    assert (out["recency_days"] >= 0).all()


# ── cluster ────────────────────────────────────────────────────────────────────


def test_cluster_rfm_segment_column(crm_df: pd.DataFrame) -> None:
    """R-05: rfm_segment 컬럼 존재."""
    rfm = build_rfm_features(crm_df, _REF)
    out = cluster(rfm, n_clusters=2)
    assert "rfm_segment" in out.columns


def test_cluster_segment_count(crm_df: pd.DataFrame) -> None:
    """R-05b: 고유 세그먼트 수 ≤ n_clusters."""
    rfm = build_rfm_features(crm_df, _REF)
    out = cluster(rfm, n_clusters=3)
    assert out["rfm_segment"].nunique() <= 3


def test_cluster_original_unchanged(crm_df: pd.DataFrame) -> None:
    """R-06: 입력 rfm 불변."""
    rfm = build_rfm_features(crm_df, _REF)
    original_cols = set(rfm.columns)
    cluster(rfm, n_clusters=2)
    assert set(rfm.columns) == original_cols


# ── compute_churn_risk ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_compute_churn_risk_dataset_not_found() -> None:
    """R-07: dataset 없음 → ValueError."""
    db = AsyncMock()
    with patch("app.services.analytics.crm_service.dataset_crud") as mock_crud:
        mock_crud.get = AsyncMock(return_value=None)
        with pytest.raises(ValueError, match="not found"):
            await crm_service.compute_churn_risk(uuid.uuid4(), db)


@pytest.mark.asyncio
async def test_compute_churn_risk_returns_response(crm_df: pd.DataFrame, tmp_path: pytest.TempPathFactory) -> None:
    """R-08: 정상 흐름 → ChurnRiskResponse 반환."""
    csv_path = tmp_path / "crm.csv"  # type: ignore[operator]
    crm_df.to_csv(csv_path, index=False)

    mock_dataset = MagicMock()
    mock_dataset.file_path = str(csv_path)

    db = AsyncMock()
    with patch("app.services.analytics.crm_service.dataset_crud") as mock_crud:
        mock_crud.get = AsyncMock(return_value=mock_dataset)
        from app.schemas.crm import ChurnRiskResponse

        result = await crm_service.compute_churn_risk(uuid.uuid4(), db)

    assert isinstance(result, ChurnRiskResponse)
    assert result.total_at_risk >= 0


@pytest.mark.asyncio
async def test_compute_churn_risk_threshold_filter(crm_df: pd.DataFrame, tmp_path: pytest.TempPathFactory) -> None:
    """R-09: recency_days > threshold 고객만 포함."""
    csv_path = tmp_path / "crm2.csv"  # type: ignore[operator]
    crm_df.to_csv(csv_path, index=False)

    mock_dataset = MagicMock()
    mock_dataset.file_path = str(csv_path)

    db = AsyncMock()
    with patch("app.services.analytics.crm_service.dataset_crud") as mock_crud:
        mock_crud.get = AsyncMock(return_value=mock_dataset)
        result = await crm_service.compute_churn_risk(uuid.uuid4(), db)

    from app.core.config import settings

    for item in result.high_risk_customers:
        assert item.last_order_days_ago > settings.CHURN_RECENCY_THRESHOLD_DAYS
