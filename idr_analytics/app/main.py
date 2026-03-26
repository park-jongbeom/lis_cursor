"""FastAPI 애플리케이션 진입점."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine

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


@app.get(
    "/health",
    summary="헬스 체크",
    description="로드밸런서·오케스트레이션용 최소 생존 확인.",
    response_description="항상 status=ok",
)
async def health() -> dict[str, str]:
    return {"status": "ok"}
