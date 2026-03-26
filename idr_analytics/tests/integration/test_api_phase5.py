"""Phase 5 API 통합 검증 — plan.md §7-3 정합."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.dataset import AnalysisDataset
from app.models.user import User
from app.schemas.agent import AgentQueryResponse
from app.services.analytics.routing_service import RoutingExecutionResult
from httpx import AsyncClient

from .helpers import insert_crm_dataset, insert_scm_dataset, write_crm_csv, write_scm_csv


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_login_returns_bearer_token(client: AsyncClient, db_user: tuple[User, str, str]) -> None:
    _u, plain_pw, uname = db_user
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": uname, "password": plain_pw},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("token_type") == "bearer"
    assert "access_token" in body and len(body["access_token"]) > 20


@pytest.mark.asyncio
async def test_login_invalid_password_401(client: AsyncClient, db_user: tuple[User, str, str]) -> None:
    _u, _pw, uname = db_user
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": uname, "password": "wrong-password"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_reissues_token(client: AsyncClient, db_user: tuple[User, str, str]) -> None:
    _u, plain_pw, uname = db_user
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": uname, "password": plain_pw},
    )
    token = login.json()["access_token"]
    r = await client.post(
        "/api/v1/auth/refresh",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("token_type") == "bearer"
    assert len(body["access_token"]) > 20


@pytest.mark.asyncio
async def test_post_scm_forecast_202_with_job_id(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_user: tuple[User, str, str],
    tmp_path: Path,
) -> None:
    user = db_user[0]
    p = tmp_path / "scm.csv"
    write_scm_csv(p)
    ds = await insert_scm_dataset(user.id, str(p.resolve()), 65)
    body = {
        "dataset_id": str(ds.id),
        "target_column": "y",
        "date_column": "ds",
        "group_by": "test_code",
        "test_codes": ["T1"],
        "forecast_days": 7,
    }
    r = await client.post("/api/v1/scm/forecast", json=body, headers=auth_headers)
    assert r.status_code == 202, r.text
    data = r.json()
    assert data.get("status") == "pending"
    assert data.get("job_id")


@pytest.mark.asyncio
async def test_get_scm_restock_alert_compact_under_4kb(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_user: tuple[User, str, str],
    tmp_path: Path,
) -> None:
    user = db_user[0]
    p = tmp_path / "scm2.csv"
    write_scm_csv(p)
    ds = await insert_scm_dataset(user.id, str(p.resolve()), 65)
    r = await client.get(
        "/api/v1/scm/restock-alert",
        params={
            "dataset_id": str(ds.id),
            "target_column": "y",
            "date_column": "ds",
            "group_by": "test_code",
            "compact": True,
        },
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    raw = json.dumps(r.json())
    assert len(raw.encode("utf-8")) <= 4096


@pytest.mark.asyncio
async def test_get_crm_churn_risk_compact_shape(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_user: tuple[User, str, str],
    tmp_path: Path,
) -> None:
    user = db_user[0]
    p = tmp_path / "crm.csv"
    write_crm_csv(p)
    ds = await insert_crm_dataset(user.id, str(p.resolve()), 6)
    r = await client.get(
        "/api/v1/crm/churn-risk",
        params={"dataset_id": str(ds.id), "top_n": 20, "compact": True},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "high_risk_count" in data
    assert "top_customers" in data
    assert "summary" in data
    assert isinstance(data["top_customers"], list)


@pytest.mark.asyncio
async def test_get_crm_churn_risk_full_has_high_risk_customers(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_user: tuple[User, str, str],
    tmp_path: Path,
) -> None:
    user = db_user[0]
    p = tmp_path / "crm2.csv"
    write_crm_csv(p)
    ds = await insert_crm_dataset(user.id, str(p.resolve()), 6)
    r = await client.get(
        "/api/v1/crm/churn-risk",
        params={"dataset_id": str(ds.id), "compact": False},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "high_risk_customers" in data
    assert "analysis_date" in data
    assert "total_at_risk" in data


@pytest.mark.asyncio
async def test_post_crm_cluster_202(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_user: tuple[User, str, str],
    tmp_path: Path,
) -> None:
    user = db_user[0]
    p = tmp_path / "crm3.csv"
    write_crm_csv(p)
    ds = await insert_crm_dataset(user.id, str(p.resolve()), 6)
    r = await client.post(
        "/api/v1/crm/cluster",
        json={"dataset_id": str(ds.id), "n_clusters": 2},
        headers=auth_headers,
    )
    assert r.status_code == 202, r.text
    assert r.json().get("job_id")


@pytest.mark.asyncio
async def test_dataset_list_requires_auth(client: AsyncClient) -> None:
    r = await client.get("/api/v1/datasets")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_forecast_forbidden_for_other_owner(
    client: AsyncClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
) -> None:
    """다른 사용자 소유 dataset_id로 예측 요청 시 403."""
    other_id = uuid.uuid4()
    other_name = f"other_{other_id.hex[:8]}"
    pw_hash = hash_password("x")
    async with async_session_factory() as db:
        other = User(
            id=other_id,
            username=other_name,
            hashed_password=pw_hash,
        )
        db.add(other)
        await db.commit()
    ds: AnalysisDataset | None = None
    try:
        p = tmp_path / "scm_other.csv"
        write_scm_csv(p)
        ds = await insert_scm_dataset(other_id, str(p.resolve()), 65)
        body = {
            "dataset_id": str(ds.id),
            "target_column": "y",
            "date_column": "ds",
            "group_by": "test_code",
            "test_codes": ["T1"],
            "forecast_days": 5,
        }
        r = await client.post("/api/v1/scm/forecast", json=body, headers=auth_headers)
        assert r.status_code == 403
    finally:
        async with async_session_factory() as db:
            if ds is not None:
                row = await db.get(AnalysisDataset, ds.id)
                if row is not None:
                    await db.delete(row)
            urow = await db.get(User, other_id)
            if urow is not None:
                await db.delete(urow)
            await db.commit()


@pytest.mark.asyncio
async def test_agent_query_tier2_success_with_output_answer(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_user: tuple[User, str, str],
    tmp_path: Path,
) -> None:
    user = db_user[0]
    p = tmp_path / "crm_agent.csv"
    write_crm_csv(p)
    ds = await insert_crm_dataset(user.id, str(p.resolve()), 6)
    sid = uuid.uuid4()
    fake = AgentQueryResponse(
        session_id=sid,
        query="요약",
        answer="tier2 응답",
        supporting_data={"workflow_run_id": "wf-1", "outputs": {"output": "tier2 응답"}},
        route_used="ai_tier2",
        llm_model="claude-sonnet-4-6",
        processing_time_ms=100,
    )
    routing_res = RoutingExecutionResult(complexity=MagicMock(), agent_response=fake, pandas_result=None)
    with patch("app.api.v1.endpoints.agent.routing_service.route", new=AsyncMock(return_value=routing_res)):
        r = await client.post(
            "/api/v1/agent/query",
            json={"query": "요약", "dataset_id": str(ds.id), "query_type": 80},
            headers=auth_headers,
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["route_used"] == "ai_tier2"
    assert body["answer"] == "tier2 응답"


@pytest.mark.asyncio
async def test_agent_query_dify_http_error_mapped_to_502(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_user: tuple[User, str, str],
    tmp_path: Path,
) -> None:
    user = db_user[0]
    p = tmp_path / "crm_agent_err.csv"
    write_crm_csv(p)
    ds = await insert_crm_dataset(user.id, str(p.resolve()), 6)

    req = httpx.Request("POST", "http://localhost:8080/v1/workflows/run")
    resp = httpx.Response(
        status_code=400,
        json={"code": "invalid_param", "message": "period is required"},
        request=req,
    )
    err = httpx.HTTPStatusError("bad request", request=req, response=resp)

    with patch("app.api.v1.endpoints.agent.routing_service.route", new=AsyncMock(side_effect=err)):
        r = await client.post(
            "/api/v1/agent/query",
            json={"query": "요약", "dataset_id": str(ds.id), "query_type": 80},
            headers=auth_headers,
        )
    assert r.status_code == 502, r.text
    data = r.json()["detail"]
    assert data["code"] == "DIFY_INPUT_ERROR"
    assert data["status_code"] == 400
    assert data["upstream"]["code"] == "invalid_param"


@pytest.mark.asyncio
async def test_agent_query_dify_auth_error_mapped_to_auth_code(
    client: AsyncClient,
    auth_headers: dict[str, str],
    db_user: tuple[User, str, str],
    tmp_path: Path,
) -> None:
    user = db_user[0]
    p = tmp_path / "crm_agent_auth_err.csv"
    write_crm_csv(p)
    ds = await insert_crm_dataset(user.id, str(p.resolve()), 6)

    req = httpx.Request("POST", "http://localhost:8080/v1/workflows/run")
    resp = httpx.Response(
        status_code=401,
        json={"code": "unauthorized", "message": "invalid api key"},
        request=req,
    )
    err = httpx.HTTPStatusError("unauthorized", request=req, response=resp)

    with patch("app.api.v1.endpoints.agent.routing_service.route", new=AsyncMock(side_effect=err)):
        r = await client.post(
            "/api/v1/agent/query",
            json={"query": "요약", "dataset_id": str(ds.id), "query_type": 80},
            headers=auth_headers,
        )
    assert r.status_code == 502, r.text
    data = r.json()["detail"]
    assert data["code"] == "DIFY_AUTH_ERROR"
    assert data["status_code"] == 401
