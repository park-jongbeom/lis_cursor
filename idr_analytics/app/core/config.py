"""애플리케이션 설정 (Pydantic BaseSettings)."""

from __future__ import annotations

import json
from typing import Any, cast

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # FastAPI
    APP_ENV: str = "development"
    SECRET_KEY: str
    ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    INTERNAL_BYPASS_ENABLED: bool = False
    INTERNAL_BYPASS_BEARER_TOKEN: str = ""
    INTERNAL_BYPASS_USERNAME: str = "admin"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # File uploads (dataset CSV 저장 경로)
    DATA_UPLOAD_DIR: str = "./data/uploads"

    # 교육용 /ide 정적 가이드 — 비우면 main.py 가 repo/demo/ide·/app/demo/ide 를 자동 탐색
    IDE_STATIC_ROOT: str | None = Field(default=None, description="demo/ide 절대 경로(선택)")

    # Analysis routing
    AI_ESCALATION_THRESHOLD: int = 70
    PANDAS_MAX_ROWS: int = 2_000_000

    # LLM
    ANTHROPIC_API_KEY: str
    LLM_MODEL: str = "claude-sonnet-4-6"
    LLM_MAX_TOKENS: int = 4096

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # Dify (rootless podman: 8080:80). 키·워크플로 ID는 콘솔 발급 전까지 비워 두면 Tier 1만 동작.
    DIFY_API_BASE_URL: str = "http://localhost:8080/v1"
    DIFY_API_KEY: str = ""
    DIFY_WORKFLOW_ID: str = ""

    # SCM / CRM
    PROPHET_CHANGEPOINT_SCALE: float = 0.05
    FORECAST_DEFAULT_DAYS: int = 30
    KMEANS_DEFAULT_CLUSTERS: int = 4
    CHURN_RECENCY_THRESHOLD_DAYS: int = 90

    @field_validator("IDE_STATIC_ROOT", mode="before")
    @classmethod
    def empty_ide_root_to_none(cls, v: Any) -> str | None:
        if v is None or v == "":
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return str(v).strip()

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return cast(list[str], json.loads(v))
        if v is None:
            return ["http://localhost:3000"]
        return cast(list[str], v)


settings = Settings()
