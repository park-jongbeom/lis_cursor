"""get_current_user / require_admin 단위 테스트.

DB 연결 없이 AsyncMock과 jose.jwt Mock으로 의존성 로직만 검증한다.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from fastapi import HTTPException
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession


def _make_user(role: str = "user", is_active: bool = True) -> User:
    user = User()
    user.id = uuid.uuid4()
    user.username = "testuser"
    user.hashed_password = "hashed"
    user.role = role
    user.is_active = is_active
    return user


def _make_mock_db(user: User | None) -> AsyncMock:
    """scalar_one_or_none()이 user를 반환하는 가짜 AsyncSession을 반환한다."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_session.execute.return_value = mock_result
    return mock_session


# ────────────────────────────────────────────────────────────────
# get_current_user
# ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_current_user_valid_token() -> None:
    """유효한 JWT sub → User 반환."""
    user = _make_user()
    db = _make_mock_db(user)

    with patch("app.core.dependencies.jwt.decode") as mock_decode:
        mock_decode.return_value = {"sub": str(user.id)}
        result = await get_current_user(token="valid.token.here", db=db)

    assert result is user


@pytest.mark.asyncio
async def test_get_current_user_invalid_token_raises_401() -> None:
    """손상된 토큰 → JWTError → 401."""
    db = _make_mock_db(None)

    with patch("app.core.dependencies.jwt.decode", side_effect=JWTError("bad token")):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="bad.token", db=db)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_sub_raises_401() -> None:
    """`sub` 필드 없는 payload → 401."""
    db = _make_mock_db(None)

    with patch("app.core.dependencies.jwt.decode", return_value={}):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="no.sub.token", db=db)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_user_not_found_raises_401() -> None:
    """DB에서 User가 없으면 → 401."""
    db = _make_mock_db(None)

    with patch("app.core.dependencies.jwt.decode", return_value={"sub": str(uuid.uuid4())}):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="valid.but.no.user", db=db)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_uuid_raises_401() -> None:
    """`sub`가 UUID 형식이 아닌 경우 → 401."""
    db = _make_mock_db(None)

    with patch("app.core.dependencies.jwt.decode", return_value={"sub": "not-a-uuid"}):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="bad.uuid.token", db=db)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_internal_bypass_success_in_development() -> None:
    """개발환경 + 내부 우회 활성화 + 토큰 일치 시 admin 사용자 반환."""
    user = _make_user(role="admin")
    user.username = "admin"
    db = _make_mock_db(user)

    with (
        patch("app.core.dependencies.settings.APP_ENV", "development"),
        patch("app.core.dependencies.settings.INTERNAL_BYPASS_ENABLED", True),
        patch("app.core.dependencies.settings.INTERNAL_BYPASS_BEARER_TOKEN", "shared-token"),
        patch("app.core.dependencies.settings.INTERNAL_BYPASS_USERNAME", "admin"),
        patch("app.core.dependencies.jwt.decode") as mock_decode,
    ):
        result = await get_current_user(token="shared-token", db=db)

    assert result is user
    mock_decode.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_user_internal_bypass_user_missing_raises_401() -> None:
    """우회 토큰이 맞아도 매핑 사용자 미존재면 401."""
    db = _make_mock_db(None)

    with (
        patch("app.core.dependencies.settings.APP_ENV", "development"),
        patch("app.core.dependencies.settings.INTERNAL_BYPASS_ENABLED", True),
        patch("app.core.dependencies.settings.INTERNAL_BYPASS_BEARER_TOKEN", "shared-token"),
        patch("app.core.dependencies.settings.INTERNAL_BYPASS_USERNAME", "admin"),
        patch("app.core.dependencies.jwt.decode") as mock_decode,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="shared-token", db=db)

    assert exc_info.value.status_code == 401
    mock_decode.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_user_internal_bypass_disabled_outside_development() -> None:
    """development 외 환경에서는 동일 토큰도 우회하지 않고 JWT 검증으로 진행."""
    db = _make_mock_db(None)

    with (
        patch("app.core.dependencies.settings.APP_ENV", "production"),
        patch("app.core.dependencies.settings.INTERNAL_BYPASS_ENABLED", True),
        patch("app.core.dependencies.settings.INTERNAL_BYPASS_BEARER_TOKEN", "shared-token"),
        patch("app.core.dependencies.jwt.decode", side_effect=JWTError("bad token")) as mock_decode,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="shared-token", db=db)

    assert exc_info.value.status_code == 401
    mock_decode.assert_called_once()


# ────────────────────────────────────────────────────────────────
# require_admin
# ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_require_admin_with_admin_role() -> None:
    """role == 'admin' → 정상 반환."""
    admin_user = _make_user(role="admin")
    result = await require_admin(current_user=admin_user)
    assert result is admin_user


@pytest.mark.asyncio
async def test_require_admin_with_user_role_raises_403() -> None:
    """role == 'user' → 403."""
    regular_user = _make_user(role="user")
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(current_user=regular_user)
    assert exc_info.value.status_code == 403
