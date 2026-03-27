"""`demo/sample_data/*.csv` 업로드 → DB 메타 · 동기 분석 API 검증.

`demo/sample_data/SAMPLE_DATA_TEST_PLAN.md` TC-SCM/CRM/BI 필수선을 pytest로 재현한다.
ARQ(예측·클러스터 폴링)는 본 파일에서 다루지 않는다.

파일명 `test_api_sample_*`: 수집 순서상 `test_arq_worker_integration`(Prophet·executor)보다 **앞**에 두어,
전역 async 엔진·이벤트 루프 불일치(`attached to a different loop`)를 피한다.
"""

from __future__ import annotations

import csv
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _sample_path(name: str) -> Path:
    p = _repo_root() / "demo" / "sample_data" / name
    if not p.is_file():
        msg = f"Missing sample CSV: {p}"
        raise AssertionError(msg)
    return p


def _csv_data_row_count(path: Path) -> int:
    """헤더 제외 데이터 행 수 — `demo/sample_data` 확장 시 하드코딩 대신 사용."""
    with path.open(newline="", encoding="utf-8") as f:
        rows = sum(1 for _ in csv.reader(f))
    return max(rows - 1, 0)


@pytest.mark.asyncio
async def test_demo_scm_sample_upload_db_and_restock(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    csv_path = _sample_path("scm_sample.csv")
    expect_rows = _csv_data_row_count(csv_path)
    r = await client.post(
        "/api/v1/datasets/upload",
        files={"file": ("scm_sample.csv", csv_path.read_bytes(), "text/csv")},
        data={"dataset_name": "integration_scm_sample", "dataset_type": "scm"},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["row_count"] == expect_rows
    assert {"order_date", "test_code", "order_qty"} <= set(body["columns"])

    ds_id = uuid.UUID(body["dataset_id"])
    r_pf = await client.get(f"/api/v1/datasets/{ds_id}/profile", headers=auth_headers)
    assert r_pf.status_code == 200, r_pf.text
    prof = r_pf.json()
    assert prof["row_count"] == expect_rows
    assert prof["dataset_name"] == "integration_scm_sample"

    r2 = await client.get(
        "/api/v1/scm/restock-alert",
        params={
            "dataset_id": str(ds_id),
            "target_column": "order_qty",
            "date_column": "order_date",
            "group_by": "test_code",
            "compact": "false",
        },
        headers=auth_headers,
    )
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert "items" in data or "forecasts" in data


@pytest.mark.asyncio
async def test_demo_crm_sample_upload_db_and_churn(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    csv_path = _sample_path("crm_sample.csv")
    expect_rows = _csv_data_row_count(csv_path)
    r = await client.post(
        "/api/v1/datasets/upload",
        files={"file": ("crm_sample.csv", csv_path.read_bytes(), "text/csv")},
        data={"dataset_name": "integration_crm_sample", "dataset_type": "crm"},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["row_count"] == expect_rows
    assert "customer_code" in body["columns"]
    assert "order_date" in body["columns"]
    assert "order_amount" in body["columns"]

    ds_id = uuid.UUID(body["dataset_id"])
    r_pf = await client.get(f"/api/v1/datasets/{ds_id}/profile", headers=auth_headers)
    assert r_pf.status_code == 200
    assert r_pf.json()["row_count"] == expect_rows

    r2 = await client.get(
        f"/api/v1/crm/churn-risk?dataset_id={ds_id}&compact=false",
        headers=auth_headers,
    )
    assert r2.status_code == 200, r2.text
    churn = r2.json()
    assert "high_risk_customers" in churn
    assert isinstance(churn["high_risk_customers"], list)


@pytest.mark.asyncio
async def test_demo_bi_sample_upload_db_heatmap_yoy(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    csv_path = _sample_path("bi_sample.csv")
    expect_rows = _csv_data_row_count(csv_path)
    r = await client.post(
        "/api/v1/datasets/upload",
        files={"file": ("bi_sample.csv", csv_path.read_bytes(), "text/csv")},
        data={"dataset_name": "integration_bi_sample", "dataset_type": "bi"},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["row_count"] == expect_rows
    assert {"period", "region", "test_code", "value", "year"} <= set(body["columns"])

    ds_id = uuid.UUID(body["dataset_id"])
    r_pf = await client.get(f"/api/v1/datasets/{ds_id}/profile", headers=auth_headers)
    assert r_pf.status_code == 200
    assert r_pf.json()["row_count"] == expect_rows

    r_h = await client.get(
        "/api/v1/bi/regional-heatmap",
        params={
            "dataset_id": str(ds_id),
            "period": "2024-01",
            "compact": "false",
            "test_category": "all",
            "period_col": "period",
            "region_col": "region",
            "value_col": "value",
            "test_col": "test_code",
        },
        headers=auth_headers,
    )
    assert r_h.status_code == 200, r_h.text
    heat = r_h.json()
    assert "heatmap" in heat
    assert len(heat["heatmap"]) >= 1

    r_y = await client.get(
        "/api/v1/bi/yoy-comparison",
        params={
            "dataset_id": str(ds_id),
            "year_col": "year",
            "value_col": "value",
            "compact": "false",
        },
        headers=auth_headers,
    )
    assert r_y.status_code == 200, r_y.text
    yoy = r_y.json()
    assert "yoy_by_year" in yoy
    assert "2023" in yoy["yoy_by_year"] or "2024" in yoy["yoy_by_year"]
