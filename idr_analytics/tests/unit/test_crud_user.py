"""CRUDUser 단위 테스트."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.crud.crud_user import user_crud
from app.models.user import User


def _make_db() -> AsyncMock:
    db = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_get_by_username_found() -> None:
    """C-09: 일치하는 username → User 반환."""
    db = _make_db()
    expected = User()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = expected
    db.execute.return_value = result_mock

    user = await user_crud.get_by_username(db, "alice")
    assert user is expected
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_username_not_found() -> None:
    """C-09b: 없는 username → None."""
    db = _make_db()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute.return_value = result_mock

    user = await user_crud.get_by_username(db, "nobody")
    assert user is None
