"""통합 테스트용 CSV 작성·DB 시드 헬퍼."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from pathlib import Path

from app.db.session import async_session_factory
from app.models.dataset import AnalysisDataset


async def insert_crm_dataset(owner_id: uuid.UUID, csv_path_str: str, row_count: int) -> AnalysisDataset:
    ds_id = uuid.uuid4()
    columns_json: dict[str, object] = {
        "columns": ["customer_code", "order_date", "order_amount"],
        "dtypes": {"customer_code": "object", "order_date": "object", "order_amount": "int64"},
        "null_counts": {"customer_code": 0, "order_date": 0, "order_amount": 0},
    }
    ds = AnalysisDataset(
        id=ds_id,
        name="integration_crm",
        dataset_type="crm",
        file_path=csv_path_str,
        row_count=row_count,
        columns_json=columns_json,
        profile_json=None,
        owner_id=owner_id,
    )
    async with async_session_factory() as db:
        db.add(ds)
        await db.commit()
        await db.refresh(ds)
    return ds


async def insert_scm_dataset(owner_id: uuid.UUID, csv_path_str: str, row_count: int) -> AnalysisDataset:
    ds_id = uuid.uuid4()
    columns_json: dict[str, object] = {
        "columns": ["ds", "test_code", "y"],
        "dtypes": {"ds": "object", "test_code": "object", "y": "int64"},
        "null_counts": {"ds": 0, "test_code": 0, "y": 0},
    }
    ds = AnalysisDataset(
        id=ds_id,
        name="integration_scm",
        dataset_type="scm",
        file_path=csv_path_str,
        row_count=row_count,
        columns_json=columns_json,
        profile_json=None,
        owner_id=owner_id,
    )
    async with async_session_factory() as db:
        db.add(ds)
        await db.commit()
        await db.refresh(ds)
    return ds


def write_crm_csv(path: Path) -> int:
    """고객 5명 이상 — KMeans(n_clusters=4) 최소 샘플 수 충족."""
    lines = [
        "customer_code,order_date,order_amount",
        "old_a,2020-01-15,100",
        "old_a,2020-03-20,80",
        "old_b,2019-06-01,50",
        "old_c,2019-08-01,60",
        "old_d,2021-01-01,40",
        "new_e,2025-02-01,500",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines) - 1


def write_scm_csv(path: Path) -> int:
    lines = ["ds,test_code,y"]
    start = date(2024, 1, 1)
    for i in range(65):
        d = start + timedelta(days=i)
        lines.append(f"{d.isoformat()},T1,{10 + i}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 65


async def insert_bi_dataset(owner_id: uuid.UUID, csv_path_str: str, row_count: int) -> AnalysisDataset:
    ds_id = uuid.uuid4()
    columns_json: dict[str, object] = {
        "columns": ["period", "region", "value", "test_code"],
        "dtypes": {
            "period": "object",
            "region": "object",
            "value": "int64",
            "test_code": "object",
        },
        "null_counts": {"period": 0, "region": 0, "value": 0, "test_code": 0},
    }
    ds = AnalysisDataset(
        id=ds_id,
        name="integration_bi",
        dataset_type="bi",
        file_path=csv_path_str,
        row_count=row_count,
        columns_json=columns_json,
        profile_json=None,
        owner_id=owner_id,
    )
    async with async_session_factory() as db:
        db.add(ds)
        await db.commit()
        await db.refresh(ds)
    return ds


def write_bi_csv(path: Path) -> int:
    """지역·기간 트렌드용 최소 샘플(regional_trend 그룹별 2기간 이상)."""
    lines = [
        "period,region,value,test_code",
        "2026-Q1,SEOUL,10,A",
        "2026-Q2,SEOUL,12,A",
        "2026-Q1,BUSAN,5,B",
        "2026-Q2,BUSAN,6,B",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines) - 1
