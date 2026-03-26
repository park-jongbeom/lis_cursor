"""CRUDDataset 단위 테스트."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.crud.crud_dataset import dataset_crud
from app.models.dataset import AnalysisDataset


def _make_db() -> AsyncMock:
    db = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_get_multi_by_owner_calls_execute() -> None:
    """C-10: owner_id 필터 포함 쿼리 실행 확인."""
    db = _make_db()
    items = [AnalysisDataset(), AnalysisDataset()]
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = items
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    db.execute.return_value = result_mock

    owner_id = uuid.uuid4()
    out = await dataset_crud.get_multi_by_owner(db, owner_id, skip=0, limit=50)

    assert out == items
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_multi_by_owner_returns_empty_list() -> None:
    """C-10b: 소유자 데이터 없음 → 빈 리스트."""
    db = _make_db()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = []
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    db.execute.return_value = result_mock

    out = await dataset_crud.get_multi_by_owner(db, uuid.uuid4())
    assert out == []
