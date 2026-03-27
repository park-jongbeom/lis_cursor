"""에이전트 쿼리 — 복잡도 라우팅 + Dify."""

import json
import uuid
from datetime import UTC, datetime
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
        # period 컬럼이 없으면 대표 날짜 컬럼에서 YYYY-MM를 추론해 Dify 입력 요구(period)를 보완한다.
        for col in ("order_date", "date", "created_at", "updated_at"):
            if col not in df.columns:
                continue
            s = pd.to_datetime(df[col], errors="coerce")
            s = s.dropna()
            if s.empty:
                continue
            return s.max().strftime("%Y-%m")
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


def _fallback_dataset_summary(query: str, df: pd.DataFrame) -> str:
    q = query.lower()
    cols = [str(c) for c in df.columns]
    parts: list[str] = [
        f"데이터셋 요약: 총 {len(df)}행, {len(cols)}개 컬럼.",
        f"주요 컬럼: {', '.join(cols[:8])}" + (" ..." if len(cols) > 8 else ""),
    ]
    if {"test_code", "order_qty"} <= set(cols):
        qty = pd.to_numeric(df["order_qty"], errors="coerce").fillna(0)
        if any(k in q for k in ("상위", "top", "많", "순위")):
            grp = (
                df.assign(_qty=qty)
                .groupby("test_code", dropna=False)["_qty"]
                .sum(numeric_only=True)
                .sort_values(ascending=False)
                .head(3)
            )
            if not grp.empty:
                top = ", ".join(f"{k}:{int(v)}" for k, v in grp.items())
                parts.append(f"검사코드별 주문합 상위: {top}")
        if any(k in q for k in ("추세", "trend", "월별", "증가", "감소")) and "order_date" in df.columns:
            s = pd.to_datetime(df["order_date"], errors="coerce")
            m = (
                pd.DataFrame({"month": s.dt.to_period("M").astype(str), "qty": qty})
                .dropna(subset=["month"])
                .groupby("month", dropna=False)["qty"]
                .sum(numeric_only=True)
                .sort_index()
            )
            if len(m) >= 2:
                delta = float(m.iloc[-1] - m.iloc[0])
                direction = "증가" if delta > 0 else ("감소" if delta < 0 else "유지")
                parts.append(
                    f"월별 총주문 추세: 시작 {m.index[0]}={m.iloc[0]:.0f}, "
                    f"최근 {m.index[-1]}={m.iloc[-1]:.0f} ({direction})."
                )
        if any(k in q for k in ("리스크", "재고", "부족", "경고")):
            grp2 = (
                df.assign(_qty=qty)
                .groupby("test_code", dropna=False)["_qty"]
                .mean(numeric_only=True)
                .sort_values(ascending=False)
                .head(1)
            )
            if not grp2.empty:
                code = str(grp2.index[0])
                val = float(grp2.iloc[0])
                parts.append(f"재고 리스크 관점: 평균 주문량이 높은 `{code}`(평균 {val:.1f}) 우선 모니터링 권장.")
    if {"customer_code", "order_amount"} <= set(cols):
        cust_n = int(df["customer_code"].astype(str).nunique())
        amt = float(pd.to_numeric(df["order_amount"], errors="coerce").fillna(0).sum())
        parts.append(f"고객 수(고유): {cust_n}, 주문금액 합계: {amt:,.0f}")
    if {"region", "value"} <= set(cols):
        reg = df.groupby("region", dropna=False)["value"].sum(numeric_only=True).sort_values(ascending=False).head(3)
        if not reg.empty:
            top_reg = ", ".join(f"{k}:{float(v):,.0f}" for k, v in reg.items())
            parts.append(f"지역별 값 합계 상위: {top_reg}")
    return " ".join(parts)


def _build_dify_http_error_detail(exc: httpx.HTTPStatusError) -> dict[str, Any]:
    status_code = exc.response.status_code if exc.response is not None else 502
    detail: dict[str, Any] = {
        "code": "DIFY_HTTP_ERROR",
        "message": "Dify workflow request failed",
        "status_code": status_code,
    }

    upstream_json: dict[str, Any] | None = None
    if exc.response is not None:
        try:
            parsed = exc.response.json()
            if isinstance(parsed, dict):
                upstream_json = parsed
                detail["upstream"] = parsed
            else:
                detail["upstream"] = exc.response.text
        except Exception:
            detail["upstream"] = exc.response.text

    up_text = ""
    if isinstance(detail.get("upstream"), str):
        up_text = detail["upstream"].lower()
    if status_code == 404 or "page not found" in up_text or "404" in up_text[:80]:
        detail["hint"] = (
            "Dify가 404를 반환했습니다. (1) `DIFY_API_BASE_URL`은 `http(s)://호스트:포트/v1` 형태 — "
            "브라우저 주소창의 `/apps` URL을 그대로 넣지 말 것. (2) Dify가 다른 머신이면 "
            "uvicorn 호스트에서 닿는 Tailscale·LAN IP + 포트(예 `:8080/v1`). "
            "(3) `DIFY_WORKFLOW_ID`는 Studio/API에서 확인한 UUID만. "
            "(4) `poetry run python scripts/verify_dify_upstream.py --dataset-id <UUID>` 로 동일 요청 재현."
        )

    if status_code in (401, 403):
        detail["code"] = "DIFY_AUTH_ERROR"
        detail["message"] = "Dify authentication/authorization failed"
        return detail

    if status_code == 400 and upstream_json is not None:
        up_code = str(upstream_json.get("code", "")).lower()
        up_msg = str(upstream_json.get("message", "")).lower()
        if up_code == "invalid_param" or "required" in up_msg:
            detail["code"] = "DIFY_INPUT_ERROR"
            detail["message"] = "Dify workflow input validation failed"

    return detail


@router.post(
    "/query",
    response_model=AgentQueryResponse,
    summary="에이전트 질의",
    description=(
        "복잡도에 따라 Tier1(Pandas)·Tier2(Dify 워크플로)로 라우팅합니다. "
        "FORECAST/CLUSTER/TREND/AGGREGATION은 `dataset_id` 및 컬럼 파라미터가 필요할 수 있습니다."
    ),
    response_description="답변·라우트·세션 ID(결과는 Redis에 24h 캐시)",
)
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
            reference_date=datetime.now(UTC),
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

    # Tier2 Dify 워크플로 입력에 `period` 필수인 경우가 많음 — CSV에서 못 추론하면 UTC 기준 당월로 보강
    period = (body.aggregation_period or "").strip()
    if not period and df is not None:
        inferred = _infer_period(df)
        if inferred:
            period = inferred
    if not period:
        period = datetime.now(UTC).strftime("%Y-%m")
    ai_inputs: dict[str, str] = {"period": period}

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
        detail = _build_dify_http_error_detail(exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from exc
    except httpx.RequestError as exc:
        code = "DIFY_TIMEOUT_ERROR" if isinstance(exc, httpx.TimeoutException) else "DIFY_REQUEST_ERROR"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": code,
                "message": str(exc),
                "hint": (
                    "Dify API에 연결하지 못했습니다. 공인 lis(§0)는 uvicorn이 돌아가는 **같은 PC**에서 "
                    "Dify로 HTTP 요청을 보냅니다. `DIFY_API_BASE_URL`은 그 PC에서 "
                    "`curl`로 열리는 주소여야 합니다. `http://localhost:8080/v1`은 **그 PC에** "
                    "Dify compose가 떠 있을 때만 유효하고, Dify가 원격만 있으면 "
                    "Tailscale·내부 IP·공인 API URL로 바꾸세요."
                ),
            },
        ) from exc

    out_sid = body.session_id or uuid.uuid4()
    if exec_result.agent_response is not None:
        response = exec_result.agent_response.model_copy(update={"session_id": out_sid})
        if (
            (not response.answer.strip())
            or response.answer.startswith("Dify 워크플로 실행은 완료되었지만 출력 텍스트가 비어 있습니다.")
        ) and df is not None:
            # Dify 워크플로 출력 키가 비어 있는 경우, 데모 연속성을 위해 데이터셋 기반 요약으로 보완
            response = response.model_copy(update={"answer": _fallback_dataset_summary(body.query, df)})
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


@router.get(
    "/query/{session_id}",
    summary="에이전트 세션 결과 조회",
    description="`/agent/query` 직후 저장된 동일 세션 응답을 Redis에서 조회합니다.",
    response_description="AgentQueryResponse JSON",
)
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
