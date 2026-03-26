"""CRM 클러스터·이탈·RFM."""

import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.job_poll import get_arq_job_view
from app.crud.crud_dataset import dataset_crud
from app.db.session import get_db
from app.models.dataset import AnalysisDataset
from app.models.user import User
from app.schemas.crm import ChurnRiskCompactCustomer, ChurnRiskCompactResponse, ClusterRequest
from app.services.analytics.crm_service import crm_service

router = APIRouter()


async def _require_owner_dataset(
    db: AsyncSession,
    dataset_id: uuid.UUID,
    user: User,
) -> AnalysisDataset:
    row = await dataset_crud.get(db, dataset_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    if row.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not owner of this dataset")
    return row


@router.post("/cluster", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_cluster(
    body: ClusterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    await _require_owner_dataset(db, body.dataset_id, current_user)
    arq_redis = request.app.state.arq_redis
    job = await arq_redis.enqueue_job(
        "cluster_job",
        str(body.dataset_id),
        body.n_clusters,
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Job enqueue failed")
    return {"job_id": job.job_id, "status": "pending"}


@router.get("/cluster/{job_id}")
async def poll_cluster(
    job_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    _ = current_user
    return await get_arq_job_view(request.app.state.arq_redis, job_id)


@router.get("/churn-risk")
async def churn_risk(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    top_n: int = 20,
    compact: bool = False,
) -> dict[str, Any]:
    await _require_owner_dataset(db, dataset_id, current_user)
    t0 = time.perf_counter()
    try:
        result = await crm_service.compute_churn_risk(dataset_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    elapsed = int((time.perf_counter() - t0) * 1000)
    result = result.model_copy(update={"processing_time_ms": elapsed})
    if not compact:
        return result.model_dump()
    tops = result.high_risk_customers[:top_n]
    customers = [
        ChurnRiskCompactCustomer(code=c.customer_code, name=c.customer_name, risk_score=c.churn_risk_score)
        for c in tops
    ]
    summary = f"고위험 {result.total_at_risk}명 중 상위 {len(customers)}명 요약"
    cr = ChurnRiskCompactResponse(
        high_risk_count=result.total_at_risk,
        top_customers=customers,
        cluster_count=settings.KMEANS_DEFAULT_CLUSTERS,
        summary=summary,
    )
    return cr.model_dump()


@router.get("/rfm-summary")
async def rfm_summary(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    compact: bool = False,
) -> dict[str, Any]:
    await _require_owner_dataset(db, dataset_id, current_user)
    try:
        full = await crm_service.compute_rfm_summary(dataset_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if not compact:
        return full
    return {
        "customer_count": full["customer_count"],
        "cluster_count": full["cluster_count"],
        "summary": f"고객 {full['customer_count']}명, 세그먼트 {len(full['segment_distribution'])}종",
    }
