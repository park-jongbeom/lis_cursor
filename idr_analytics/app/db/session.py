"""Async SQLAlchemy engine and session factory."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",
    # asyncpg 연결이 유휴 상태에서 끊긴 경우 재사용 전에 ping으로 감지한다.
    pool_pre_ping=True,
    # 장시간 유지된 연결 재사용을 피해서 "connection is closed" 가능성을 줄인다.
    pool_recycle=1800,
)

async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
