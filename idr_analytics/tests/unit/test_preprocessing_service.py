"""preprocessing_service 단위 테스트."""

from __future__ import annotations

import pandas as pd
import pytest
from app.services.data.preprocessing_service import preprocessing_service


@pytest.fixture()
def time_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2026-01-03", "2026-01-01", "2026-01-02"],
            "value": [30.0, 10.0, None],
        }
    )


@pytest.fixture()
def mixed_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "num": [1.0, None, 3.0, None],
            "cat": ["a", None, "a", "b"],
        }
    )


# ── build_time_index ───────────────────────────────────────────────────────────


def test_build_time_index_creates_datetime_index(time_df: pd.DataFrame) -> None:
    """P-01: 결과 인덱스가 DatetimeIndex이고 정렬됨."""
    out = preprocessing_service.build_time_index(time_df, "date")
    assert isinstance(out.index, pd.DatetimeIndex)
    assert out.index.is_monotonic_increasing


def test_build_time_index_original_unchanged(time_df: pd.DataFrame) -> None:
    """P-02: 원본 DataFrame 불변."""
    original_cols = list(time_df.columns)
    preprocessing_service.build_time_index(time_df, "date")
    assert list(time_df.columns) == original_cols
    assert "date" in time_df.columns  # 원본에 date 컬럼 유지


def test_build_time_index_ffill_applied(time_df: pd.DataFrame) -> None:
    """P-01b: ffill 적용 후 NaN 없음."""
    out = preprocessing_service.build_time_index(time_df, "date")
    assert out["value"].isna().sum() == 0


# ── fill_missing ───────────────────────────────────────────────────────────────


def test_fill_missing_numeric_no_nan(mixed_df: pd.DataFrame) -> None:
    """P-03: 수치 결측 ffill/bfill 후 NaN 없음."""
    out = preprocessing_service.fill_missing(mixed_df)
    assert out["num"].isna().sum() == 0


def test_fill_missing_categorical_mode(mixed_df: pd.DataFrame) -> None:
    """P-04: 범주 결측 → 최빈값으로 채움."""
    out = preprocessing_service.fill_missing(mixed_df)
    assert out["cat"].isna().sum() == 0
    assert out["cat"].iloc[1] == "a"  # 최빈값 'a'


def test_fill_missing_original_unchanged(mixed_df: pd.DataFrame) -> None:
    """P-04b: 원본 불변."""
    preprocessing_service.fill_missing(mixed_df)
    assert mixed_df["num"].isna().sum() == 2


# ── add_lag_features ───────────────────────────────────────────────────────────


def test_add_lag_features_creates_columns() -> None:
    """P-05: lag_1, lag_7 컬럼 생성."""
    df = pd.DataFrame({"val": list(range(10))})
    out = preprocessing_service.add_lag_features(df, "val", lags=(1, 7))
    assert "lag_1" in out.columns
    assert "lag_7" in out.columns


def test_add_lag_features_shift_correct() -> None:
    """P-05b: lag_1 값이 shift(1) 결과와 일치."""
    df = pd.DataFrame({"val": [10, 20, 30, 40, 50]})
    out = preprocessing_service.add_lag_features(df, "val", lags=(1,))
    assert out["lag_1"].iloc[1] == 10.0
    assert out["lag_1"].iloc[2] == 20.0


def test_add_lag_features_missing_column_raises() -> None:
    """P-06: 없는 컬럼 → KeyError."""
    df = pd.DataFrame({"val": [1, 2, 3]})
    with pytest.raises(KeyError):
        preprocessing_service.add_lag_features(df, "nonexistent")


def test_add_lag_features_original_unchanged() -> None:
    """P-05c: 원본 불변."""
    df = pd.DataFrame({"val": [1, 2, 3]})
    preprocessing_service.add_lag_features(df, "val", lags=(1,))
    assert "lag_1" not in df.columns


# ── normalize ──────────────────────────────────────────────────────────────────


def test_normalize_creates_scaled_columns() -> None:
    """P-07: {col}_scaled 컬럼 생성, 원본 컬럼 유지."""
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})
    out = preprocessing_service.normalize(df, ["a", "b"])
    assert "a_scaled" in out.columns
    assert "b_scaled" in out.columns
    assert "a" in out.columns  # 원본 유지


def test_normalize_scaled_values_standardized() -> None:
    """P-07b: 스케일링 후 mean ≈ 0, std ≈ 1."""

    df = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0, 5.0]})
    out = preprocessing_service.normalize(df, ["x"])
    assert abs(float(out["x_scaled"].mean())) < 1e-10
    assert abs(float(out["x_scaled"].std(ddof=0)) - 1.0) < 1e-10


def test_normalize_missing_column_raises() -> None:
    """P-08: 없는 컬럼 → KeyError."""
    df = pd.DataFrame({"a": [1.0, 2.0]})
    with pytest.raises(KeyError):
        preprocessing_service.normalize(df, ["nonexistent"])


def test_normalize_original_unchanged() -> None:
    """P-07c: 원본 불변."""
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0]})
    preprocessing_service.normalize(df, ["a"])
    assert "a_scaled" not in df.columns
