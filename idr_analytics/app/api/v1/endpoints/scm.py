"""SCM 수요 예측·재고 알림·계절성."""

import uuid
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.job_poll import get_arq_job_view
from app.crud.crud_dataset import dataset_crud
from app.db.session import get_db
from app.models.dataset import AnalysisDataset
from app.models.user import User
from app.schemas.scm import (
    ForecastCompactItem,
    ForecastCompactResponse,
    ForecastRequest,
)
from app.services.analytics.scm_service import scm_service
from app.services.data.ingestion_service import ingestion_service

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


@router.post(
    "/forecast",
    status_code=status.HTTP_202_ACCEPTED,
    summary="수요 예측 잡 등록",
    description="ARQ `forecast_job`을 큐에 넣고 `job_id`를 반환합니다. 결과는 폴링 엔드포인트로 조회합니다.",
    response_description="job_id, status=pending",
)
async def enqueue_forecast(
    body: ForecastRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    await _require_owner_dataset(db, body.dataset_id, current_user)
    arq_redis = request.app.state.arq_redis
    job = await arq_redis.enqueue_job(
        "forecast_job",
        str(body.dataset_id),
        body.model_dump(mode="json"),
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Job enqueue failed")
    return {"job_id": job.job_id, "status": "pending"}


@router.get(
    "/forecast/{job_id}",
    summary="수요 예측 잡 폴링",
    description="Redis에 저장된 ARQ 잡 상태·결과를 조회합니다.",
    response_description="잡 상태 및 완료 시 예측 결과",
)
async def poll_forecast(
    job_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    _ = current_user
    return await get_arq_job_view(request.app.state.arq_redis, job_id)


@router.get(
    "/restock-alert",
    summary="재보추 알림",
    description="예측 기반 재고·보추 검토 후보를 산출합니다.",
    response_description="compact=false 전체 / compact=true 4KB 이하 요약",
)
async def restock_alert(
    dataset_id: uuid.UUID,
    target_column: str,
    date_column: str,
    group_by: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    compact: bool = Query(
        False,
        description="true면 Dify·LLM용 4KB 이하 요약만 반환합니다.",
    ),
    test_codes: str | None = None,
    forecast_days: int = 30,
) -> dict[str, Any]:
    row = await _require_owner_dataset(db, dataset_id, current_user)
    df, _ = ingestion_service.read_csv_validated(row.file_path)
    codes = [x.strip() for x in test_codes.split(",")] if test_codes else None
    report = await scm_service.restock_alert_report(
        df,
        target_column,
        date_column,
        group_by,
        test_codes=codes,
        forecast_days=forecast_days,
    )
    if not compact:
        forecasts = report["forecasts"]
        return {
            "restock_alerts": report["restock_alerts"],
            "items": report["items"],
            "forecasts": [f.model_dump() for f in forecasts],
        }
    forecasts_obj = report["forecasts"]
    high: list[ForecastCompactItem] = []
    for f in forecasts_obj:
        if not f.predictions:
            continue
        high.append(
            ForecastCompactItem(
                test_code=f.test_code,
                predicted_qty=float(f.predictions[-1].yhat),
                trend=f.trend_direction,
            )
        )
    high.sort(key=lambda x: x.predicted_qty, reverse=True)
    top = high[:20]
    summary = f"재보추 검토 후보 {len(top)}건, 알림 {report['restock_alerts']}건"
    return ForecastCompactResponse(
        forecast_period_days=forecast_days,
        high_demand_items=top,
        restock_alerts=int(report["restock_alerts"]),
        summary=summary,
    ).model_dump()


@router.get(
    "/seasonal-pattern",
    summary="계절성 패턴",
    description="검사항목별 주간 등 계절성 요약을 반환합니다.",
    response_description="compact=false 상세 / compact=true 요약 카운트",
)
async def seasonal_pattern(
    dataset_id: uuid.UUID,
    target_column: str,
    date_column: str,
    group_by: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    compact: bool = Query(
        False,
        description="true면 Dify·LLM용 4KB 이하 요약만 반환합니다.",
    ),
    test_codes: str | None = None,
    forecast_days: int = 30,
) -> dict[str, Any]:
    row = await _require_owner_dataset(db, dataset_id, current_user)
    df, _ = ingestion_service.read_csv_validated(row.file_path)
    codes = [x.strip() for x in test_codes.split(",")] if test_codes else None
    rep = await scm_service.seasonal_pattern_report(
        df,
        target_column,
        date_column,
        group_by,
        test_codes=codes,
        forecast_days=forecast_days,
    )
    if not compact:
        return {"patterns": rep["patterns"], "forecast_days": rep["forecast_days"]}
    patterns = cast(list[dict[str, Any]], rep["patterns"])
    weekly_true = sum(1 for p in patterns if bool(cast(dict[str, Any], p.get("seasonality", {})).get("weekly")))
    summary = f"검사항목 {len(patterns)}건 중 주간계절성 {weekly_true}건"
    return {
        "item_count": len(patterns),
        "weekly_seasonality_count": weekly_true,
        "summary": summary,
    }
