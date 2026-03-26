"""Pandas preprocessing — copy-in, copy-out (no in-place mutation)."""

from __future__ import annotations

import pandas as pd
from sklearn.preprocessing import StandardScaler


class PreprocessingService:
    def build_time_index(self, df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        out = df.copy()
        out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
        out = out.set_index(date_col).sort_index()
        out = out.ffill()
        return out.copy()

    def fill_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        num_cols = out.select_dtypes(include=["number"]).columns
        for col in num_cols:
            out[col] = out[col].ffill()
            out[col] = out[col].bfill()
        cat_cols = out.select_dtypes(exclude=["number"]).columns
        for col in cat_cols:
            mode = out[col].mode(dropna=True)
            fill_val = mode.iloc[0] if len(mode) else None
            out[col] = out[col].fillna(fill_val)
        return out.copy()

    def add_lag_features(self, df: pd.DataFrame, col: str, lags: tuple[int, ...] = (1, 7, 30)) -> pd.DataFrame:
        """단순 시프트 lag: `lag_n` = n행(또는 시점) 이전 값 (rolling 아님)."""
        out = df.copy()
        if col not in out.columns:
            msg = f"Column {col!r} not in DataFrame"
            raise KeyError(msg)
        for n in lags:
            out[f"lag_{n}"] = out[col].shift(n)
        return out.copy()

    def normalize(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        """지정 컬럼을 StandardScaler 후 `{col}_scaled` 로 저장 (원본 유지)."""
        out = df.copy()
        for c in cols:
            if c not in out.columns:
                msg = f"Column {c!r} not in DataFrame"
                raise KeyError(msg)
        scaler = StandardScaler()
        scaled = scaler.fit_transform(out[cols].astype(float))
        for i, c in enumerate(cols):
            out[f"{c}_scaled"] = scaled[:, i]
        return out.copy()


preprocessing_service = PreprocessingService()
