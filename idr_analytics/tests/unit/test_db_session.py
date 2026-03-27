"""DB 세션 엔진 설정 회귀 테스트."""

from app.db.session import engine


def test_engine_pool_pre_ping_enabled() -> None:
    """유휴/끊긴 asyncpg 연결 재사용 전에 ping 검증이 활성화되어야 한다."""
    assert getattr(engine.sync_engine.pool, "_pre_ping", False) is True


def test_engine_pool_recycle_seconds() -> None:
    """장시간 유지 연결 재사용 방지를 위해 recycle 시간이 설정되어야 한다."""
    assert getattr(engine.sync_engine.pool, "_recycle", -1) == 1800
