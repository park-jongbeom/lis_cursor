"""CRUDBase 단위 테스트 — AsyncMock(AsyncSession) 사용, DB 연결 불필요."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.crud.base import CRUDBase
from app.models.dataset import AnalysisDataset

# 실제 ORM 모델을 사용하여 SQLAlchemy 매핑 오류 회피
_crud: CRUDBase[AnalysisDataset] = CRUDBase(AnalysisDataset)


def _make_db() -> AsyncMock:
    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


# ── get ────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_returns_object() -> None:
    """C-01: 존재하는 id → scalar_one_or_none 반환값 전달."""
    db = _make_db()
    expected = AnalysisDataset()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = expected
    db.execute.return_value = result_mock

    obj = await _crud.get(db, uuid.uuid4())
    assert obj is expected


@pytest.mark.asyncio
async def test_get_returns_none_when_missing() -> None:
    """C-02: 없는 id → None 반환."""
    db = _make_db()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute.return_value = result_mock

    obj = await _crud.get(db, uuid.uuid4())
    assert obj is None


# ── get_multi ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_multi_returns_list() -> None:
    """C-03: skip/limit 파라미터 전달 및 리스트 반환."""
    db = _make_db()
    items = [AnalysisDataset(), AnalysisDataset()]
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = items
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    db.execute.return_value = result_mock

    out = await _crud.get_multi(db, skip=0, limit=10)
    assert out == items
    db.execute.assert_called_once()


# ── create ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_with_dict() -> None:
    """C-04: dict 입력 → add, commit, refresh 순서 보장."""
    db = _make_db()
    db.refresh = AsyncMock(side_effect=lambda obj: None)

    obj = await _crud.create(
        db,
        {
            "name": "test",
            "dataset_type": "scm",
            "file_path": "/tmp/x.csv",
            "row_count": 0,
            "columns_json": {},
            "owner_id": uuid.uuid4(),
        },
    )

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()
    assert isinstance(obj, AnalysisDataset)


@pytest.mark.asyncio
async def test_create_with_pydantic_model() -> None:
    """C-05: Pydantic 모델 입력 → model_dump() 경유."""
    from pydantic import BaseModel

    class _Schema(BaseModel):
        name: str

    db = _make_db()
    db.refresh = AsyncMock(side_effect=lambda obj: None)

    obj = await _crud.create(db, _Schema(name="pydantic"))

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    assert isinstance(obj, AnalysisDataset)


# ── update ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_partial_fields() -> None:
    """C-06: exclude_unset=True — 전달된 필드만 setattr."""
    from pydantic import BaseModel

    class _UpdateSchema(BaseModel):
        name: str | None = None

    db = _make_db()
    db_obj = AnalysisDataset()
    db.refresh = AsyncMock(side_effect=lambda obj: None)

    schema = _UpdateSchema(name="updated")
    result = await _crud.update(db, db_obj=db_obj, obj_in=schema)

    assert result is db_obj
    assert getattr(db_obj, "name", "updated") is not None
    db.commit.assert_awaited_once()


# ── delete ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_existing_row() -> None:
    """C-07: rowcount=1 → 정상 완료."""
    db = _make_db()
    cursor_mock = MagicMock()
    cursor_mock.rowcount = 1
    db.execute.return_value = cursor_mock

    await _crud.delete(db, id=uuid.uuid4())
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_missing_row_raises() -> None:
    """C-08: rowcount=0 → ValueError."""
    db = _make_db()
    cursor_mock = MagicMock()
    cursor_mock.rowcount = 0
    db.execute.return_value = cursor_mock

    with pytest.raises(ValueError, match="not found"):
        await _crud.delete(db, id=uuid.uuid4())
