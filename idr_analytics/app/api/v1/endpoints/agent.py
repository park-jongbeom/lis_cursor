"""에이전트 쿼리 — 복잡도 라우팅 + Dify."""

import json
import uuid
from datetime import datetime
from typing import Any, cast

import httpx
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.routing import QueryType, RoutingRequest
from app.crud.crud_dataset import dataset_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.agent import AgentQueryRequest, AgentQueryResponse
from app.services.analytics.routing_service import (
    BIRegionalTrendContext,
    BITopTestsContext,
    CRMClusterContext,
    SCMForecastContext,
    routing_service,
)
from app.services.data.ingestion_service import ingestion_service

router = APIRouter()

_AGENT_KEY_PREFIX = "idr:agent:session:"


def _infer_period(df: pd.DataFrame) -> str | None:
    if "period" not in df.columns:
        return None
    vals = df["period"].dropna().astype(str)
    if vals.empty:
        return None
    return vals.max()


def _pandas_answer(body: AgentQueryRequest, obj: object) -> str:
    if isinstance(obj, list):
        dumped: list[dict[str, Any]] = []
        for x in obj:
            if hasattr(x, "model_dump"):
                dumped.append(x.model_dump())
            else:
                dumped.append({"value": str(x)})
        return json.dumps(dumped, ensure_ascii=False, default=str)[:50000]
    if isinstance(obj, pd.DataFrame):
        return obj.head(500).to_json(orient="records", date_format="iso")[:50000]
    return str(obj)[:50000]


@router.post("/query", response_model=AgentQueryResponse)
async def agent_query(
    body: AgentQueryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentQueryResponse:
    if body.query_type is not None:
        try:
            qt = QueryType(body.query_type)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid query_type",
            ) from exc
    else:
        qt = QueryType.NATURAL_LANGUAGE

    pandas_needs_dataset = qt in (
        QueryType.FORECAST,
        QueryType.CLUSTER,
        QueryType.TREND,
        QueryType.AGGREGATION,
    )

    df: pd.DataFrame | None = None
    row_count = 0
    if body.dataset_id is not None:
        row = await dataset_crud.get(db, body.dataset_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        if row.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not owner of this dataset")
        df, _ = ingestion_service.read_csv_validated(row.file_path)
        row_count = len(df)

    if pandas_needs_dataset and df is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="dataset_id is required for this query_type",
        )

    routing_req = RoutingRequest(query_type=qt, row_count=row_count, cross_table=False)

    pandas_context: SCMForecastContext | CRMClusterContext | BIRegionalTrendContext | BITopTestsContext | None = None
    if df is not None and qt == QueryType.FORECAST:
        if not (body.target_column and body.date_column and body.group_by_column):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FORECAST requires target_column, date_column, group_by_column",
            )
        pandas_context = SCMForecastContext(
            df=df,
            target_col=body.target_column,
            date_col=body.date_column,
            group_col=body.group_by_column,
            periods=body.forecast_days,
        )
    elif df is not None and qt == QueryType.CLUSTER:
        pandas_context = CRMClusterContext(
            df=df,
            reference_date=datetime.utcnow(),
            n_clusters=body.n_clusters,
        )
    elif df is not None and qt == QueryType.TREND:
        if not (body.period_column and body.region_column and body.value_column):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TREND requires period_column, region_column, value_column",
            )
        pandas_context = BIRegionalTrendContext(
            df=df,
            period_col=body.period_column,
            region_col=body.region_column,
            value_col=body.value_column,
        )
    elif df is not None and qt == QueryType.AGGREGATION:
        period = body.aggregation_period or ""
        pandas_context = BITopTestsContext(
            df=df,
            period=period,
            top_n=body.top_n,
            period_col=body.period_column or "period",
            test_col=body.test_column or "test_code",
            value_col=body.value_column or "value",
        )

    ai_inputs: dict[str, str] | None = None
    period = (body.aggregation_period or "").strip()
    if not period and df is not None:
        inferred = _infer_period(df)
        if inferred:
            period = inferred
    if period:
        ai_inputs = {"period": period}

    try:
        exec_result = await routing_service.route(
            routing_req,
            db,
            pandas_context=pandas_context,
            nl_query=body.query,
            dataset_id=body.dataset_id,
            session_id=body.session_id,
            ai_inputs=ai_inputs,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except httpx.HTTPStatusError as exc:
        detail: dict[str, Any] = {
            "code": "DIFY_HTTP_ERROR",
            "message": "Dify workflow request failed",
            "status_code": exc.response.status_code if exc.response is not None else 502,
        }
        if exc.response is not None:
            try:
                detail["upstream"] = exc.response.json()
            except Exception:
                detail["upstream"] = exc.response.text
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "DIFY_REQUEST_ERROR", "message": str(exc)},
        ) from exc

    out_sid = body.session_id or uuid.uuid4()
    if exec_result.agent_response is not None:
        response = exec_result.agent_response.model_copy(update={"session_id": out_sid})
    elif exec_result.pandas_result is not None:
        response = AgentQueryResponse(
            session_id=out_sid,
            query=body.query,
            answer=_pandas_answer(body, exec_result.pandas_result),
            supporting_data={"complexity": exec_result.complexity.model_dump()},
            route_used="pandas_tier1",
            llm_model=None,
            processing_time_ms=None,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Empty routing result",
        )

    redis = request.app.state.arq_redis
    key = _AGENT_KEY_PREFIX + str(response.session_id)
    await redis.set(
        key,
        json.dumps(response.model_dump(mode="json")),
        ex=86400,
    )
    return response


@router.get("/query/{session_id}")
async def get_agent_query(
    session_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    _ = current_user
    redis = request.app.state.arq_redis
    raw = await redis.get(_AGENT_KEY_PREFIX + str(session_id))
    if raw is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return cast(dict[str, Any], json.loads(raw))
