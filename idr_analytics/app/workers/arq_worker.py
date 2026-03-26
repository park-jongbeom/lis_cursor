"""ARQ 워커 — Prophet/RFM/BI 트렌드 배치 잡."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from typing import Any

from arq.connections import RedisSettings

from app.core.config import settings
from app.crud.crud_dataset import dataset_crud
from app.db.session import async_session_factory
from app.services.analytics.bi_service import bi_service
from app.services.analytics.crm_service import CRM_CUSTOMER_CODE, CRM_REQUIRED, crm_service
from app.services.analytics.scm_service import scm_service
from app.services.data.ingestion_service import ingestion_service


async def forecast_job(ctx: dict[str, Any], dataset_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    target_col = str(payload["target_column"])
    date_col = str(payload["date_column"])
    group_col = str(payload["group_by"])
    forecast_days = int(payload.get("forecast_days", 30))
    test_codes = payload.get("test_codes")
    if test_codes is not None and not isinstance(test_codes, list):
        test_codes = None
    codes = [str(x) for x in test_codes] if test_codes else None

    async with async_session_factory() as db:
        row = await dataset_crud.get(db, uuid.UUID(dataset_id))
    if row is None:
        msg = f"AnalysisDataset {dataset_id} not found"
        raise ValueError(msg)

    df, _ = ingestion_service.read_csv_validated(row.file_path)
    if codes:
        df = df[df[group_col].astype(str).isin(set(codes))].copy()
    forecasts = await scm_service.forecast(df, target_col, date_col, group_col, forecast_days)
    elapsed = int((time.perf_counter() - t0) * 1000)
    return {
        "model_used": "prophet_or_arima",
        "forecasts": [f.model_dump() for f in forecasts],
        "processing_time_ms": elapsed,
    }


async def cluster_job(ctx: dict[str, Any], dataset_id: str, n_clusters: int) -> dict[str, Any]:
    t0 = time.perf_counter()
    async with async_session_factory() as db:
        row = await dataset_crud.get(db, uuid.UUID(dataset_id))
    if row is None:
        msg = f"AnalysisDataset {dataset_id} not found"
        raise ValueError(msg)

    df, _ = ingestion_service.read_csv_validated(row.file_path, required_columns=CRM_REQUIRED)
    rfm = crm_service.build_rfm_features(df, datetime.utcnow())
    clustered = crm_service.cluster(rfm, n_clusters=n_clusters)
    elapsed = int((time.perf_counter() - t0) * 1000)
    sample = clustered.head(100)
    records: list[dict[str, Any]] = []
    for _, r in sample.iterrows():
        rec: dict[str, Any] = {
            "customer_code": str(r[CRM_CUSTOMER_CODE]),
            "recency_days": int(r["recency_days"]),
            "rfm_segment": str(r["rfm_segment"]),
        }
        records.append(rec)
    return {
        "cluster_count": n_clusters,
        "customer_total": int(len(clustered)),
        "sample": records,
        "processing_time_ms": elapsed,
    }


async def trend_job(
    ctx: dict[str, Any],
    dataset_id: str,
    period_col: str,
    region_col: str,
    value_col: str,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    async with async_session_factory() as db:
        row = await dataset_crud.get(db, uuid.UUID(dataset_id))
    if row is None:
        msg = f"AnalysisDataset {dataset_id} not found"
        raise ValueError(msg)

    df, _ = ingestion_service.read_csv_validated(row.file_path)
    trend_df = bi_service.regional_trend(df, period_col, region_col, value_col)
    elapsed = int((time.perf_counter() - t0) * 1000)
    raw = trend_df.to_json(orient="records", date_format="iso")
    rows = json.loads(raw)
    return {"rows": rows, "processing_time_ms": elapsed}


class WorkerSettings:
    functions = [forecast_job, cluster_job, trend_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    keep_result = 3600
