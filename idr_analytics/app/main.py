"""FastAPI 애플리케이션 진입점 (Phase 1 스켈레톤)."""

from fastapi import FastAPI

app = FastAPI(
    title="IDR Analytics",
    description="IDR 시스템 데이터 분석 AI 에이전트 백엔드",
    version="0.1.0",
)


@app.get("/health")  # type: ignore[misc]
async def health() -> dict[str, str]:
    return {"status": "ok"}
