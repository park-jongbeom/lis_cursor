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

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

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

    # Dify
    DIFY_API_BASE_URL: str = "http://localhost/v1"
    DIFY_API_KEY: str
    DIFY_WORKFLOW_ID: str

    # SCM / CRM
    PROPHET_CHANGEPOINT_SCALE: float = 0.05
    FORECAST_DEFAULT_DAYS: int = 30
    KMEANS_DEFAULT_CLUSTERS: int = 4
    CHURN_RECENCY_THRESHOLD_DAYS: int = 90

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return cast(list[str], json.loads(v))
        if v is None:
            return ["http://localhost:3000"]
        return cast(list[str], v)


settings = Settings()
