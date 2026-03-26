"""CSV ingestion and column profile (DataFrame immutability)."""

from __future__ import annotations

import pandas as pd


def read_csv_validated(
    file_path: str,
    required_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, int]:
    df = pd.read_csv(file_path)
    df = df.copy()
    if required_columns:
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            msg = f"Missing required columns: {missing}"
            raise ValueError(msg)
    row_count = len(df)
    return df, row_count


def build_columns_profile(df: pd.DataFrame) -> dict[str, object]:
    """DB `columns_json` / `DatasetProfileResponse` 조립용 구조."""
    work = df.copy()
    columns = list(work.columns)
    dtypes = {c: str(work[c].dtype) for c in columns}
    null_counts = {c: int(work[c].isna().sum()) for c in columns}
    return {
        "columns": columns,
        "dtypes": dtypes,
        "null_counts": null_counts,
    }


class IngestionService:
    read_csv_validated = staticmethod(read_csv_validated)
    build_columns_profile = staticmethod(build_columns_profile)


ingestion_service = IngestionService()
