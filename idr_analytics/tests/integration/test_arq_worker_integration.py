"""ARQ 워커 잡 통합 검증 — 실 DB·실 CSV·실 서비스(Prophet 등).

`make test`(test-infra-up, Postgres 15433) 전제. Redis·워커 프로세스는 불필요(잡 함수 직접 호출).

`forecast_job`이 `run_in_executor`(Prophet)를 사용하므로, 테스트 함수마다 이벤트 루프가
바뀌면 전역 `async_engine`/asyncpg 연결이 깨질 수 있다. 시나리오는 **단일** `@pytest.mark.asyncio`
테스트 안에서 순차 실행한다.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from app.crud.crud_dataset import dataset_crud
from app.db.session import async_session_factory
from app.models.user import User
from app.workers.arq_worker import cluster_job, forecast_job, trend_job

from .helpers import (
    insert_bi_dataset,
    insert_crm_dataset,
    insert_scm_dataset,
    write_bi_csv,
    write_crm_csv,
    write_scm_csv,
)


async def _delete_dataset_row(dataset_id: uuid.UUID) -> None:
    async with async_session_factory() as db:
        await dataset_crud.delete(db, id=dataset_id)


@pytest.mark.asyncio
async def test_arq_worker_integration_suite(
    db_user: tuple[User, str, str],
    tmp_path: Path,
) -> None:
    user = db_user[0]

    # --- forecast_job 성공 ---
    p_fc = tmp_path / "arq_forecast.csv"
    write_scm_csv(p_fc)
    ds_fc = await insert_scm_dataset(user.id, str(p_fc.resolve()), 65)
    try:
        payload_fc: dict[str, object] = {
            "target_column": "y",
            "date_column": "ds",
            "group_by": "test_code",
            "forecast_days": 7,
            "test_codes": ["T1"],
        }
        out_fc = await forecast_job({}, str(ds_fc.id), payload_fc)
        assert out_fc["model_used"] == "prophet_or_arima"
        assert out_fc["forecasts"]
        assert isinstance(out_fc["processing_time_ms"], int)
        assert out_fc["processing_time_ms"] >= 0
    finally:
        await _delete_dataset_row(ds_fc.id)
        p_fc.unlink(missing_ok=True)

    # --- forecast_job 데이터셋 없음 ---
    payload_missing: dict[str, object] = {
        "target_column": "y",
        "date_column": "ds",
        "group_by": "test_code",
        "forecast_days": 7,
    }
    with pytest.raises(ValueError, match="not found"):
        await forecast_job({}, str(uuid.uuid4()), payload_missing)

    # --- cluster_job 성공 ---
    p_cl = tmp_path / "arq_cluster.csv"
    rc = write_crm_csv(p_cl)
    ds_cl = await insert_crm_dataset(user.id, str(p_cl.resolve()), rc)
    try:
        out_cl = await cluster_job({}, str(ds_cl.id), 2)
        assert out_cl["cluster_count"] == 2
        assert out_cl["customer_total"] >= 1
        assert isinstance(out_cl["sample"], list)
        assert isinstance(out_cl["processing_time_ms"], int)
        assert out_cl["processing_time_ms"] >= 0
    finally:
        await _delete_dataset_row(ds_cl.id)
        p_cl.unlink(missing_ok=True)

    with pytest.raises(ValueError, match="not found"):
        await cluster_job({}, str(uuid.uuid4()), 2)

    # --- trend_job 성공 ---
    p_tr = tmp_path / "arq_trend.csv"
    rb = write_bi_csv(p_tr)
    ds_tr = await insert_bi_dataset(user.id, str(p_tr.resolve()), rb)
    try:
        out_tr = await trend_job({}, str(ds_tr.id), "period", "region", "value")
        assert isinstance(out_tr["rows"], list)
        assert out_tr["rows"]
        assert isinstance(out_tr["processing_time_ms"], int)
        assert out_tr["processing_time_ms"] >= 0
    finally:
        await _delete_dataset_row(ds_tr.id)
        p_tr.unlink(missing_ok=True)

    with pytest.raises(ValueError, match="not found"):
        await trend_job({}, str(uuid.uuid4()), "period", "region", "value")
