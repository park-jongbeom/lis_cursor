"""BI regional trends, YoY, top tests."""

from __future__ import annotations

import pandas as pd


class BIService:
    def regional_trend(
        self,
        df: pd.DataFrame,
        period_col: str,
        region_col: str,
        value_col: str,
    ) -> pd.DataFrame:
        """기간·지역별 합계 후, 정렬된 기간 인덱스에서 전기 대비 성장률(`growth_vs_prev`) 컬럼."""
        work = df.copy()
        for c in (period_col, region_col, value_col):
            if c not in work.columns:
                msg = f"Column {c!r} not in DataFrame"
                raise KeyError(msg)
        agg: pd.DataFrame = (
            work.groupby([period_col, region_col], as_index=False)
            .agg({value_col: "sum"})
            .sort_values(by=[region_col, period_col])
        )
        out_rows: list[dict[str, object]] = []
        for region, g in agg.groupby(region_col, sort=False):
            g = g.sort_values(period_col).reset_index(drop=True)
            prev: float | None = None
            for _, row in g.iterrows():
                cur = float(row[value_col])
                if prev is None or prev == 0.0:
                    growth = 0.0
                else:
                    growth = (cur - prev) / prev
                out_rows.append(
                    {
                        period_col: row[period_col],
                        region_col: region,
                        value_col: cur,
                        "growth_vs_prev": growth,
                    }
                )
                prev = cur
        return pd.DataFrame(out_rows)

    def yoy_comparison(self, df: pd.DataFrame, year_col: str, value_col: str) -> dict[str, float]:
        """연도별 합계 집계 후 직전 연도 대비 증감률(소수; 0.14 = 14% 증가). 키는 연도 문자열."""
        work = df.copy()
        for c in (year_col, value_col):
            if c not in work.columns:
                msg = f"Column {c!r} not in DataFrame"
                raise KeyError(msg)
        by_year = work.groupby(year_col, sort=True)[value_col].sum()
        out: dict[str, float] = {}
        prev_val: float | None = None
        for y in by_year.index:
            cur = float(by_year.loc[y])
            key = str(y)
            if prev_val is None or prev_val == 0:
                out[key] = 0.0
            else:
                out[key] = (cur - prev_val) / prev_val
            prev_val = cur
        return out

    def top_tests(
        self,
        df: pd.DataFrame,
        period: str,
        top_n: int,
        *,
        period_col: str = "period",
        test_col: str = "test_code",
        value_col: str = "value",
    ) -> pd.DataFrame:
        """`period_col == period` 행만 남기고 `test_col` 기준 `value_col` 합 상위 `top_n`."""
        work = df.copy()
        for c in (test_col, value_col):
            if c not in work.columns:
                msg = f"Column {c!r} not in DataFrame"
                raise KeyError(msg)
        if period_col in work.columns:
            work = work[work[period_col].astype(str) == str(period)]
        ranked: pd.DataFrame = (
            work.groupby(test_col, as_index=False)
            .agg({value_col: "sum"})
            .sort_values(by=value_col, ascending=False)
            .head(top_n)
        )
        return ranked.copy()


bi_service = BIService()
