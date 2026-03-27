"""LIS 화면형 샘플을 데모용 SCM/CRM/BI CSV로 변환한다.

입력: lis_orders_sample.csv
출력:
  - scm_from_lis.csv  (order_date,test_code,order_qty)
  - crm_from_lis.csv  (customer_code,customer_name,order_date,order_amount)
  - bi_from_lis.csv   (period,year,region,test_code,value)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = [
    "request_date",
    "customer_code",
    "customer_name",
    "region",
    "test_code",
    "sales_amount",
]


def _read_lis_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        msg = f"입력 CSV 필수 컬럼 누락: {missing}"
        raise ValueError(msg)
    out = df.copy()
    out["request_date"] = pd.to_datetime(out["request_date"], errors="coerce")
    out["sales_amount"] = pd.to_numeric(out["sales_amount"], errors="coerce")
    out = out.dropna(subset=["request_date", "sales_amount"])
    return out


def build_scm(df: pd.DataFrame) -> pd.DataFrame:
    """SCM 데모용: 상위 코드의 주간 매출 합계를 시계열로 만든다."""
    work = df.copy()
    # LIS 원본은 코드가 잘게 분산되어 희소해지므로 상위 4개 코드만 사용한다.
    top_codes = (
        work.groupby("test_code", as_index=False)["sales_amount"]
        .sum()
        .sort_values("sales_amount", ascending=False)
        .head(4)["test_code"]
        .tolist()
    )
    work = work[work["test_code"].isin(top_codes)].copy()

    # 월요일 기준 주간 버킷으로 집계한다.
    work["order_date"] = work["request_date"].dt.to_period("W-SUN").dt.start_time
    agg = (
        work.groupby(["order_date", "test_code"], as_index=False)["sales_amount"]
        .sum()
        .rename(columns={"sales_amount": "order_qty"})
    )

    # 코드별 누락 주차를 0으로 채워서 예측 시계열을 안정화한다.
    parts: list[pd.DataFrame] = []
    for code, sub in agg.groupby("test_code", sort=False):
        sub = sub.sort_values("order_date").copy()
        full_dates = pd.date_range(sub["order_date"].min(), sub["order_date"].max(), freq="W-MON")
        expanded = (
            pd.DataFrame({"order_date": full_dates})
            .merge(sub[["order_date", "order_qty"]], on="order_date", how="left")
            .fillna({"order_qty": 0})
        )
        expanded["test_code"] = code
        expanded["order_qty"] = expanded["order_qty"].round().astype(int)
        parts.append(expanded[["order_date", "test_code", "order_qty"]])

    out = pd.concat(parts, ignore_index=True).sort_values(["test_code", "order_date"])
    out["order_date"] = out["order_date"].dt.strftime("%Y-%m-%d")
    return out


def build_crm(df: pd.DataFrame) -> pd.DataFrame:
    """CRM 데모용: 고객 주문 이력으로 정규화."""
    work = df.copy()
    work = work.rename(
        columns={
            "request_date": "order_date",
            "sales_amount": "order_amount",
        }
    )
    work["order_date"] = work["order_date"].dt.strftime("%Y-%m-%d")
    out = work[["customer_code", "customer_name", "order_date", "order_amount"]].copy()
    out = out.sort_values(["customer_code", "order_date"])
    return out


def build_bi(df: pd.DataFrame) -> pd.DataFrame:
    """BI 데모용: 월/지역/검사코드 매출 합계."""
    work = df.copy()
    work["period"] = work["request_date"].dt.to_period("M").astype(str)
    work["year"] = work["request_date"].dt.year
    agg = (
        work.groupby(["period", "year", "region", "test_code"], as_index=False)["sales_amount"]
        .sum()
        .rename(columns={"sales_amount": "value"})
        .sort_values(["period", "region", "test_code"])
    )
    return agg[["period", "year", "region", "test_code", "value"]]


def main() -> None:
    parser = argparse.ArgumentParser(description="LIS CSV -> 데모용 CSV 변환")
    parser.add_argument(
        "--input",
        default="demo/sample_data/lis_orders_sample.csv",
        help="원본 LIS CSV 경로",
    )
    parser.add_argument(
        "--out-dir",
        default="demo/sample_data",
        help="출력 디렉터리",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = _read_lis_csv(input_path)
    scm_df = build_scm(df)
    crm_df = build_crm(df)
    bi_df = build_bi(df)

    scm_path = out_dir / "scm_from_lis.csv"
    crm_path = out_dir / "crm_from_lis.csv"
    bi_path = out_dir / "bi_from_lis.csv"

    scm_df.to_csv(scm_path, index=False)
    crm_df.to_csv(crm_path, index=False)
    bi_df.to_csv(bi_path, index=False)

    print(f"[ok] input rows: {len(df)}")
    print(f"[ok] {scm_path} rows={len(scm_df)}")
    print(f"[ok] {crm_path} rows={len(crm_df)}")
    print(f"[ok] {bi_path} rows={len(bi_df)}")


if __name__ == "__main__":
    main()
