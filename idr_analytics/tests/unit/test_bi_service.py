"""BIService 단위 테스트."""

from __future__ import annotations

import pandas as pd
import pytest
from app.services.analytics.bi_service import bi_service


@pytest.fixture()
def regional_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "period": ["2025Q1", "2025Q2", "2025Q3", "2025Q1", "2025Q2", "2025Q3"],
            "region": ["서울", "서울", "서울", "부산", "부산", "부산"],
            "value": [100.0, 120.0, 150.0, 80.0, 80.0, 100.0],
        }
    )


@pytest.fixture()
def yoy_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2024, 2024, 2025, 2025],
            "value": [100.0, 200.0, 150.0, 250.0],
        }
    )


@pytest.fixture()
def top_tests_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "period": ["202601", "202601", "202601", "202602", "202602"],
            "test_code": ["BRCA1", "HPV", "BRCA1", "HPV", "BRCA2"],
            "value": [50.0, 30.0, 70.0, 40.0, 20.0],
        }
    )


# ── regional_trend ─────────────────────────────────────────────────────────────


def test_regional_trend_growth_column(regional_df: pd.DataFrame) -> None:
    """B-01: growth_vs_prev 컬럼 존재."""
    out = bi_service.regional_trend(regional_df, "period", "region", "value")
    assert "growth_vs_prev" in out.columns


def test_regional_trend_first_period_zero(regional_df: pd.DataFrame) -> None:
    """B-02: 각 지역 첫 기간 성장률 = 0.0."""
    out = bi_service.regional_trend(regional_df, "period", "region", "value")
    for region in ["서울", "부산"]:
        first = out[out["region"] == region].sort_values("period").iloc[0]
        assert first["growth_vs_prev"] == 0.0


def test_regional_trend_growth_calculation(regional_df: pd.DataFrame) -> None:
    """B-03: 전기 대비 성장률 수식 검증 (서울 Q1→Q2: (120-100)/100 = 0.2)."""
    out = bi_service.regional_trend(regional_df, "period", "region", "value")
    seoul = out[out["region"] == "서울"].sort_values("period").reset_index(drop=True)
    assert abs(seoul.loc[1, "growth_vs_prev"] - 0.2) < 1e-9


def test_regional_trend_missing_column_raises(regional_df: pd.DataFrame) -> None:
    """B-04: 필수 컬럼 누락 → KeyError."""
    with pytest.raises(KeyError):
        bi_service.regional_trend(regional_df, "period", "region", "nonexistent")


# ── yoy_comparison ─────────────────────────────────────────────────────────────


def test_yoy_comparison_returns_dict(yoy_df: pd.DataFrame) -> None:
    """B-05: 연도 키, 증감률 float 반환."""
    out = bi_service.yoy_comparison(yoy_df, "year", "value")
    assert isinstance(out, dict)
    assert "2024" in out
    assert "2025" in out
    assert isinstance(out["2025"], float)


def test_yoy_comparison_first_year_zero(yoy_df: pd.DataFrame) -> None:
    """B-06: 첫 연도 증감률 = 0.0."""
    out = bi_service.yoy_comparison(yoy_df, "year", "value")
    assert out["2024"] == 0.0


def test_yoy_comparison_rate_correct(yoy_df: pd.DataFrame) -> None:
    """B-05b: 2024 합=300, 2025 합=400 → 증감률 ≈ 0.333."""
    out = bi_service.yoy_comparison(yoy_df, "year", "value")
    expected = (400.0 - 300.0) / 300.0
    assert abs(out["2025"] - expected) < 1e-9


# ── top_tests ──────────────────────────────────────────────────────────────────


def test_top_tests_period_filter(top_tests_df: pd.DataFrame) -> None:
    """B-07: period 필터 — 해당 기간 행만 집계."""
    out = bi_service.top_tests(top_tests_df, "202601", top_n=10)
    # 202601: BRCA1=120, HPV=30
    codes = set(out["test_code"].tolist())
    assert "BRCA2" not in codes  # 202602 데이터 제외


def test_top_tests_top_n_limit(top_tests_df: pd.DataFrame) -> None:
    """B-08: 결과 행 수 ≤ top_n."""
    out = bi_service.top_tests(top_tests_df, "202601", top_n=1)
    assert len(out) <= 1


def test_top_tests_sorted_descending(top_tests_df: pd.DataFrame) -> None:
    """B-08b: 합계 내림차순 정렬."""
    out = bi_service.top_tests(top_tests_df, "202601", top_n=10)
    values = out["value"].tolist()
    assert values == sorted(values, reverse=True)


def test_top_tests_missing_column_raises(top_tests_df: pd.DataFrame) -> None:
    """B-09: 필수 컬럼 누락 → KeyError."""
    with pytest.raises(KeyError):
        bi_service.top_tests(top_tests_df, "202601", top_n=5, value_col="nonexistent")
