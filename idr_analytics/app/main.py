"""FastAPI 애플리케이션 진입점."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine

logger = logging.getLogger(__name__)

_OPENAPI_TAGS: list[dict[str, str]] = [
    {"name": "auth", "description": "JWT 로그인·토큰 갱신"},
    {"name": "datasets", "description": "CSV 업로드·목록·미리보기·프로필·삭제"},
    {"name": "scm", "description": "수요 예측(ARQ)·재보추·계절성(Tier1)"},
    {"name": "crm", "description": "RFM·클러스터(ARQ)·이탈·요약(Tier1)"},
    {"name": "bi", "description": "지역 트렌드(ARQ)·히트맵·YoY·상위 검사(Tier1)"},
    {"name": "agent", "description": "복잡도 라우팅·Dify Tier2·세션 조회"},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    arq_redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    app.state.arq_redis = arq_redis
    yield
    await arq_redis.aclose()
    await engine.dispose()


app = FastAPI(
    title="IDR Analytics API",
    description=(
        "IDR 시스템 데이터 분석 AI 에이전트 백엔드. "
        "SCM(수요 예측)·CRM(RFM·클러스터)·BI(트렌드) Tier1(Pandas)과 "
        "Tier2(Dify 워크플로) 하이브리드 라우팅을 제공합니다. "
        "Dify HTTP Request 노드 연동 시 `compact=true` 요약 응답을 우선 사용하세요."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=_OPENAPI_TAGS,
    contact={"name": "IDR Analytics"},
    license_info={"name": "Proprietary"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# 교육용 정적 가이드: .env 의 IDE_STATIC_ROOT 우선, 없으면 repo/demo/ide·Docker /app/demo/ide 자동 탐색
_pkg_root = Path(__file__).resolve().parent.parent
_IDE_CANDIDATES: tuple[Path, ...] = tuple(
    p
    for p in (
        Path(settings.IDE_STATIC_ROOT).expanduser().resolve() if settings.IDE_STATIC_ROOT else None,
        _pkg_root.parent / "demo" / "ide",  # .../idr_analytics/app/main.py → repo/demo/ide
        _pkg_root / "demo" / "ide",  # /app/app/main.py → /app/demo/ide
    )
    if p is not None
)
_IDE_STATIC_ROOT = next((p for p in _IDE_CANDIDATES if p.is_dir()), None)
if _IDE_STATIC_ROOT is not None:
    app.mount(
        "/ide",
        StaticFiles(directory=str(_IDE_STATIC_ROOT), html=True),
        name="ide",
    )
    logger.info("IDE 정적 가이드 마운트: /ide -> %s", _IDE_STATIC_ROOT)
else:
    logger.warning(
        "IDE 정적 가이드 비활성: demo/ide 없음 (후보 %s)",
        [str(p) for p in _IDE_CANDIDATES],
    )


@app.get(
    "/health",
    summary="헬스 체크",
    description="로드밸런서·오케스트레이션용 최소 생존 확인.",
    response_description="항상 status=ok",
)
async def health() -> dict[str, str]:
    return {"status": "ok"}


# 강의 데모 `demo/index.html` — 공인 `/` 는 엣지 nginx 가 동일 FastAPI 업스트림으로 프록시 (ga-server 정적 root 제거).
# Starlette 는 먼저 등록된 라우트가 우선이므로 `/api/v1`·`/ide`·`/health`·`/docs` 등 이후에 `/` 마운트.
_DEMO_CANDIDATES: tuple[Path, ...] = (_pkg_root.parent / "demo", _pkg_root / "demo")
_DEMO_STATIC_ROOT = next(
    (p for p in _DEMO_CANDIDATES if p.is_dir() and (p / "index.html").is_file()),
    None,
)
if _DEMO_STATIC_ROOT is not None:
    app.mount(
        "/",
        StaticFiles(directory=str(_DEMO_STATIC_ROOT), html=True),
        name="demo",
    )
    logger.info("강의 데모 정적 마운트: / -> %s", _DEMO_STATIC_ROOT)
else:
    logger.warning(
        "강의 데모 정적 비활성: demo/index.html 없음 (후보 %s)",
        [str(p) for p in _DEMO_CANDIDATES],
    )
