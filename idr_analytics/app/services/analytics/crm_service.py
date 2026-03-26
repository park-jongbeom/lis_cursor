"""CRM RFM, K-Means clustering, churn risk."""

from __future__ import annotations

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from typing import Any

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud.crud_dataset import dataset_crud
from app.schemas.crm import ChurnRiskItem, ChurnRiskResponse
from app.services.data.ingestion_service import read_csv_validated

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="crm_analytics")

# Gate B: 샘플/SDD 가정 컬럼명 (실제 CSV에 맞게 Phase 5에서 조정 가능)
CRM_CUSTOMER_CODE = "customer_code"
CRM_CUSTOMER_NAME = "customer_name"
CRM_ORDER_DATE = "order_date"
CRM_ORDER_AMOUNT = "order_amount"
CRM_REQUIRED = [CRM_CUSTOMER_CODE, CRM_ORDER_DATE, CRM_ORDER_AMOUNT]


def _reference_to_datetime(reference_date: date | datetime) -> pd.Timestamp:
    if isinstance(reference_date, datetime):
        return pd.Timestamp(reference_date)
    return pd.Timestamp(reference_date)


def build_rfm_features(df: pd.DataFrame, reference_date: date | datetime) -> pd.DataFrame:
    work = df.copy()
    for c in CRM_REQUIRED:
        if c not in work.columns:
            msg = f"Missing column {c!r} for RFM"
            raise KeyError(msg)
    ref = _reference_to_datetime(reference_date)
    work[CRM_ORDER_DATE] = pd.to_datetime(work[CRM_ORDER_DATE], errors="coerce")
    work = work.dropna(subset=[CRM_ORDER_DATE, CRM_ORDER_AMOUNT])
    grouped = work.groupby(CRM_CUSTOMER_CODE, as_index=False).agg(
        last_order=(CRM_ORDER_DATE, "max"),
        frequency=(CRM_ORDER_DATE, "count"),
        monetary=(CRM_ORDER_AMOUNT, "sum"),
    )
    if CRM_CUSTOMER_NAME in work.columns:
        names = work[[CRM_CUSTOMER_CODE, CRM_CUSTOMER_NAME]].drop_duplicates(subset=[CRM_CUSTOMER_CODE])
        grouped = grouped.merge(names, on=CRM_CUSTOMER_CODE, how="left")
    grouped["recency_days"] = (ref - grouped["last_order"]).dt.days.astype(int)

    def _pct_score(series: pd.Series, *, higher_is_better: bool) -> pd.Series:
        r = series.rank(pct=True, method="average", ascending=not higher_is_better)
        return (r * 4.0 + 1.0).round().clip(1, 5).astype(int)

    grouped["R_score"] = _pct_score(grouped["recency_days"], higher_is_better=False)
    grouped["F_score"] = _pct_score(grouped["frequency"], higher_is_better=True)
    grouped["M_score"] = _pct_score(grouped["monetary"], higher_is_better=True)
    return grouped.copy()


def _segment_label_from_cluster_id(cid: int, n_clusters: int) -> str:
    defaults = ["at_risk", "champions", "loyal", "lost", "hibernating", "others"]
    if cid < len(defaults):
        return defaults[cid]
    return f"segment_{cid}"


def cluster(rfm: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    out = rfm.copy()
    feature_cols = ["recency_days", "frequency", "monetary"]
    X = out[feature_cols].astype(float).to_numpy()
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    out["cluster_id"] = km.fit_predict(Xs)
    out["rfm_segment"] = out["cluster_id"].map(lambda i: _segment_label_from_cluster_id(int(i), n_clusters))
    return out.copy()


def _churn_score(recency_days: int, threshold: int) -> float:
    if threshold <= 0:
        return 0.0
    x = min(1.0, max(0.0, recency_days / float(threshold)))
    return float(round(x, 4))


def _recommended_action(segment: str, recency_days: int) -> str:
    if recency_days > settings.CHURN_RECENCY_THRESHOLD_DAYS:
        return "즉시 리텐션 콜·맞춤 프로모션 검토"
    if segment == "at_risk":
        return "방문·주문 이력 확인 후 담당자 배정"
    if segment == "lost":
        return "재활성 캠페인 또는 관계 종료 검토"
    return "정기 모니터링"


def _sync_churn_pipeline(file_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    df, _ = read_csv_validated(file_path, required_columns=CRM_REQUIRED)
    ref = datetime.now()
    rfm = build_rfm_features(df, ref)
    clustered = cluster(rfm, n_clusters=settings.KMEANS_DEFAULT_CLUSTERS)
    return rfm, clustered


def _sync_rfm_summary(file_path: str) -> dict[str, Any]:
    df, _ = read_csv_validated(file_path, required_columns=CRM_REQUIRED)
    ref = datetime.now()
    rfm = build_rfm_features(df, ref)
    clustered = cluster(rfm, n_clusters=settings.KMEANS_DEFAULT_CLUSTERS)
    seg_counts = clustered["rfm_segment"].value_counts().to_dict()
    return {
        "customer_count": int(len(clustered)),
        "avg_recency_days": float(clustered["recency_days"].mean()),
        "avg_frequency": float(clustered["frequency"].mean()),
        "avg_monetary": float(clustered["monetary"].mean()),
        "segment_distribution": {str(k): int(v) for k, v in seg_counts.items()},
        "cluster_count": int(settings.KMEANS_DEFAULT_CLUSTERS),
    }


class CRMService:
    def build_rfm_features(self, df: pd.DataFrame, reference_date: date | datetime) -> pd.DataFrame:
        return build_rfm_features(df, reference_date)

    def cluster(self, rfm: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
        return cluster(rfm, n_clusters=n_clusters)

    async def compute_churn_risk(self, dataset_id: uuid.UUID, db: AsyncSession) -> ChurnRiskResponse:
        row = await dataset_crud.get(db, dataset_id)
        if row is None:
            msg = f"AnalysisDataset {dataset_id} not found"
            raise ValueError(msg)

        loop = asyncio.get_running_loop()
        _, clustered = await loop.run_in_executor(
            _executor,
            lambda: _sync_churn_pipeline(row.file_path),
        )

        threshold = settings.CHURN_RECENCY_THRESHOLD_DAYS
        high = clustered[clustered["recency_days"] > threshold].copy()
        high = high.sort_values("recency_days", ascending=False)

        items: list[ChurnRiskItem] = []
        for _, r in high.iterrows():
            code = str(r[CRM_CUSTOMER_CODE])
            if CRM_CUSTOMER_NAME in clustered.columns and pd.notna(r.get(CRM_CUSTOMER_NAME)):
                cust_name = str(r[CRM_CUSTOMER_NAME])
            else:
                cust_name = code
            seg = str(r["rfm_segment"])
            recency = int(r["recency_days"])
            score = _churn_score(recency, threshold)
            action = _recommended_action(seg, recency)
            items.append(
                ChurnRiskItem(
                    customer_code=code,
                    customer_name=cust_name,
                    last_order_days_ago=recency,
                    churn_risk_score=score,
                    rfm_segment=seg,
                    recommended_action=action,
                )
            )

        analysis_date = date.today().isoformat()
        return ChurnRiskResponse(
            analysis_date=analysis_date,
            high_risk_customers=items,
            total_at_risk=len(items),
            processing_time_ms=None,
        )

    async def compute_rfm_summary(self, dataset_id: uuid.UUID, db: AsyncSession) -> dict[str, Any]:
        row = await dataset_crud.get(db, dataset_id)
        if row is None:
            msg = f"AnalysisDataset {dataset_id} not found"
            raise ValueError(msg)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_executor, lambda: _sync_rfm_summary(row.file_path))


crm_service = CRMService()
