"""ingestion_service 단위 테스트."""

from __future__ import annotations

import pandas as pd
import pytest
from app.services.data.ingestion_service import build_columns_profile, read_csv_validated


@pytest.fixture()
def sample_csv(tmp_path: pytest.TempPathFactory) -> str:
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "product": ["A", "B", None],
            "qty": [10, 20, 30],
        }
    )
    p = tmp_path / "sample.csv"  # type: ignore[operator]
    df.to_csv(p, index=False)
    return str(p)


# ── read_csv_validated ─────────────────────────────────────────────────────────


def test_read_csv_validated_returns_df_and_row_count(sample_csv: str) -> None:
    """I-01: 정상 CSV → (DataFrame, int) 반환, row_count 일치."""
    df, row_count = read_csv_validated(sample_csv)
    assert isinstance(df, pd.DataFrame)
    assert row_count == 3
    assert row_count == len(df)


def test_read_csv_validated_required_columns_ok(sample_csv: str) -> None:
    """I-01b: required_columns 모두 존재 → 정상 반환."""
    df, _ = read_csv_validated(sample_csv, required_columns=["date", "qty"])
    assert "date" in df.columns


def test_read_csv_validated_missing_required_column(sample_csv: str) -> None:
    """I-02: required_columns 누락 → ValueError, 메시지에 누락 컬럼명 포함."""
    with pytest.raises(ValueError, match="missing_col"):
        read_csv_validated(sample_csv, required_columns=["missing_col"])


def test_read_csv_validated_original_not_mutated(sample_csv: str) -> None:
    """I-01c: 반환된 DataFrame 수정이 원본에 영향 없음 (copy 보장)."""
    df, _ = read_csv_validated(sample_csv)
    df["new_col"] = 0
    df2, _ = read_csv_validated(sample_csv)
    assert "new_col" not in df2.columns


# ── build_columns_profile ──────────────────────────────────────────────────────


def test_build_columns_profile_keys() -> None:
    """I-03: columns, dtypes, null_counts 키 존재."""
    df = pd.DataFrame({"a": [1, 2], "b": ["x", None]})
    profile = build_columns_profile(df)
    assert "columns" in profile
    assert "dtypes" in profile
    assert "null_counts" in profile


def test_build_columns_profile_null_counts_accurate() -> None:
    """I-04: null_counts 값 정확."""
    df = pd.DataFrame({"a": [1, None, None], "b": ["x", "y", "z"]})
    profile = build_columns_profile(df)
    null_counts = profile["null_counts"]
    assert isinstance(null_counts, dict)
    assert null_counts["a"] == 2
    assert null_counts["b"] == 0


def test_build_columns_profile_columns_list() -> None:
    """I-03b: columns 리스트가 DataFrame 컬럼 순서와 일치."""
    df = pd.DataFrame({"z": [1], "a": [2], "m": [3]})
    profile = build_columns_profile(df)
    assert profile["columns"] == ["z", "a", "m"]
