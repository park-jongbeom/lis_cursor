"""통합 테스트 픽스처 — ARQ 풀 목 처리, DB 시드.

`make test`(test-infra-up) 시 Postgres(15433)와 정합.
ARQ enqueue는 `create_pool` 목으로 Redis·워커 없이 검증한다.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.user import User
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_arq_create_pool() -> object:
    """lifespan의 create_pool을 대체 — 실제 Redis·워커 없이 enqueue만 검증."""

    async def _fake_create_pool(*_a: object, **_kw: object) -> object:
        pool = MagicMock()
        job = MagicMock()
        job.job_id = "integration-test-arq-job"
        pool.enqueue_job = AsyncMock(return_value=job)
        pool.aclose = AsyncMock()
        pool.set = AsyncMock(return_value=True)
        pool.get = AsyncMock(return_value=None)
        return pool

    return _fake_create_pool


@pytest.fixture
async def client(mock_arq_create_pool: object, monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AsyncClient]:
    monkeypatch.setattr("app.main.create_pool", mock_arq_create_pool)
    from app.main import app

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
            yield ac


@pytest.fixture
async def db_user() -> AsyncIterator[tuple[User, str, str]]:
    """로그인 가능한 사용자 1명 생성 후 정리."""
    plain_pw = "Itest-Secret-9"
    uname = f"it_{uuid.uuid4().hex[:12]}"
    uid = uuid.uuid4()
    async with async_session_factory() as db:
        u = User(
            id=uid,
            username=uname,
            hashed_password=hash_password(plain_pw),
        )
        db.add(u)
        await db.commit()
        await db.refresh(u)
        try:
            yield u, plain_pw, uname
        finally:
            await db.delete(u)
            await db.commit()


@pytest.fixture
async def auth_headers(client: AsyncClient, db_user: tuple[User, str, str]) -> dict[str, str]:
    _user, plain_pw, uname = db_user
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": uname, "password": plain_pw},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
