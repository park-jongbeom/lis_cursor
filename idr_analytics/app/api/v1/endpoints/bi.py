"""BI 트렌드·히트맵·YoY·상위 검사."""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.job_poll import get_arq_job_view
from app.crud.crud_dataset import dataset_crud
from app.db.session import get_db
from app.models.dataset import AnalysisDataset
from app.models.user import User
from app.schemas.bi import (
    HeatmapCompactResponse,
    HeatmapEntry,
    HeatmapHighlight,
    HeatmapResponse,
    TrendRequest,
)
from app.services.analytics.bi_service import bi_service
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
    "/trend",
    status_code=status.HTTP_202_ACCEPTED,
    summary="지역 트렌드 잡 등록",
    description="ARQ `trend_job`을 큐에 넣어 `regional_trend` 결과를 비동기 산출합니다.",
    response_description="job_id, status=pending",
)
async def enqueue_trend(
    body: TrendRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    await _require_owner_dataset(db, body.dataset_id, current_user)
    arq_redis = request.app.state.arq_redis
    job = await arq_redis.enqueue_job(
        "trend_job",
        str(body.dataset_id),
        body.period_col,
        body.region_col,
        body.value_col,
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Job enqueue failed")
    return {"job_id": job.job_id, "status": "pending"}


@router.get(
    "/trend/{job_id}",
    summary="트렌드 잡 폴링",
    description="ARQ 잡 상태 및 완료 시 지역별 트렌드 행을 조회합니다.",
    response_description="잡 상태·결과",
)
async def poll_trend(
    job_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    _ = current_user
    return await get_arq_job_view(request.app.state.arq_redis, job_id)


@router.get(
    "/regional-heatmap",
    summary="지역 히트맵",
    description="특정 기간의 지역별 주문·YoY·상위 검사 코드를 집계합니다.",
    response_description="compact=false 전체 / compact=true Dify용 요약",
)
async def regional_heatmap(
    dataset_id: uuid.UUID,
    period: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    test_category: str = "all",
    period_col: str = "period",
    region_col: str = "region",
    value_col: str = "value",
    test_col: str = "test_code",
    compact: bool = Query(
        False,
        description="true면 Dify·LLM용 4KB 이하 요약만 반환합니다.",
    ),
) -> dict[str, Any]:
    row = await _require_owner_dataset(db, dataset_id, current_user)
    df, _ = ingestion_service.read_csv_validated(row.file_path)
    if period_col not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing column {period_col!r}",
        )
    sub = df[df[period_col].astype(str) == str(period)].copy()
    if sub.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No rows for period")
    trend_df = bi_service.regional_trend(df, period_col, region_col, value_col)
    trend_sub = trend_df[trend_df[period_col].astype(str) == str(period)].copy()
    heatmap: list[HeatmapEntry] = []
    for region, g in sub.groupby(region_col, sort=False):
        order_count = int(len(g))
        if test_col in g.columns:
            top_series = g.groupby(test_col, sort=False)[value_col].sum().sort_values(ascending=False)
            top_test = str(top_series.index[0]) if len(top_series) else ""
        else:
            top_test = ""
        gtr = trend_sub[trend_sub[region_col] == region]
        yoy = float(gtr["growth_vs_prev"].iloc[-1]) if not gtr.empty else 0.0
        heatmap.append(
            HeatmapEntry(
                region=str(region),
                order_count=order_count,
                yoy_growth=yoy,
                top_test=top_test,
            )
        )
    insight = f"{period} 기준 지역 {len(heatmap)}곳 ({test_category})"
    resp = HeatmapResponse(period=period, test_category=test_category, heatmap=heatmap, insight=insight)
    if not compact:
        return resp.model_dump()
    top_regions = [h.region for h in heatmap[:5]]
    trending_tests: list[str] = []
    seen: set[str] = set()
    for h in heatmap:
        if h.top_test and h.top_test not in seen:
            seen.add(h.top_test)
            trending_tests.append(h.top_test)
        if len(trending_tests) >= 5:
            break
    highlights = [HeatmapHighlight(region=h.region, test=h.top_test, growth_rate=h.yoy_growth) for h in heatmap[:5]]
    summary = f"{period} 상위 지역 {len(top_regions)}곳, 성장 강한 검사 {len(highlights)}건"
    return HeatmapCompactResponse(
        period=period,
        top_regions=top_regions,
        trending_tests=trending_tests,
        heatmap_highlights=highlights,
        summary=summary,
    ).model_dump()


@router.get(
    "/yoy-comparison",
    summary="전년 대비(YoY)",
    description="연도 컬럼 기준 증감률을 계산합니다.",
    response_description="연도별 YoY / compact 시 상위 연도 요약",
)
async def yoy_comparison(
    dataset_id: uuid.UUID,
    year_col: str,
    value_col: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    compact: bool = Query(
        False,
        description="true면 Dify·LLM용 4KB 이하 요약만 반환합니다.",
    ),
) -> dict[str, Any]:
    row = await _require_owner_dataset(db, dataset_id, current_user)
    df, _ = ingestion_service.read_csv_validated(row.file_path)
    rates = bi_service.yoy_comparison(df, year_col, value_col)
    if not compact:
        return {"yoy_by_year": rates}
    keys = sorted(rates.keys(), reverse=True)[:3]
    summary = ", ".join(f"{k}:{rates[k]:.1%}" for k in keys) if keys else "데이터 없음"
    return {"top_years": keys, "summary": summary}


@router.get(
    "/top-tests",
    summary="기간별 상위 검사",
    description="주어진 기간에서 검사 코드(또는 상품)별 집계 상위 N건을 반환합니다.",
    response_description="순위 테이블 / compact 시 코드·요약",
)
async def top_tests(
    dataset_id: uuid.UUID,
    period: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    top_n: int = 10,
    period_col: str = "period",
    test_col: str = "test_code",
    value_col: str = "value",
    compact: bool = Query(
        False,
        description="true면 Dify·LLM용 4KB 이하 요약만 반환합니다.",
    ),
) -> dict[str, Any]:
    row = await _require_owner_dataset(db, dataset_id, current_user)
    df, _ = ingestion_service.read_csv_validated(row.file_path)
    ranked = bi_service.top_tests(df, period, top_n, period_col=period_col, test_col=test_col, value_col=value_col)
    raw = ranked.to_json(orient="records", date_format="iso")
    rows = json.loads(raw)
    if not compact:
        return {"period": period, "ranked": rows}
    codes = [str(r.get(test_col, "")) for r in rows[:5]]
    summary = f"{period} 상위 검사 {min(len(rows), top_n)}건"
    return {"period": period, "top_test_codes": codes, "summary": summary}
