"""Settings 단위 테스트.

conftest.py에서 필수 env var를 선주입하므로 Settings()는 collection 단계에서 안전하다.
개별 테스트에서 monkeypatch로 값을 덮어써 파싱 로직을 검증한다.
"""

import pytest
from app.core.config import Settings


def test_default_llm_model() -> None:
    """LLM_MODEL 기본값 확인."""
    s = Settings()
    assert s.LLM_MODEL == "claude-sonnet-4-6"


def test_default_pandas_max_rows() -> None:
    """PANDAS_MAX_ROWS 기본값 확인."""
    s = Settings()
    assert s.PANDAS_MAX_ROWS == 2_000_000


def test_default_ai_escalation_threshold() -> None:
    """AI_ESCALATION_THRESHOLD 정수 파싱 확인 (conftest에서 '70' 주입)."""
    s = Settings()
    assert s.AI_ESCALATION_THRESHOLD == 70
    assert isinstance(s.AI_ESCALATION_THRESHOLD, int)


def test_allowed_origins_json_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """ALLOWED_ORIGINS가 JSON 문자열로 전달되면 list[str]로 파싱해야 한다."""
    monkeypatch.setenv("ALLOWED_ORIGINS", '["http://a.com", "http://b.com"]')
    s = Settings()
    assert s.ALLOWED_ORIGINS == ["http://a.com", "http://b.com"]
    assert isinstance(s.ALLOWED_ORIGINS, list)


def test_allowed_origins_default() -> None:
    """ALLOWED_ORIGINS 환경변수 없을 때 기본값 반환."""
    s = Settings()
    assert isinstance(s.ALLOWED_ORIGINS, list)
    assert len(s.ALLOWED_ORIGINS) >= 1


def test_prophet_changepoint_scale_default() -> None:
    """PROPHET_CHANGEPOINT_SCALE 기본값 float 확인."""
    s = Settings()
    assert s.PROPHET_CHANGEPOINT_SCALE == pytest.approx(0.05)


def test_kmeans_default_clusters() -> None:
    """KMEANS_DEFAULT_CLUSTERS 기본값 확인."""
    s = Settings()
    assert s.KMEANS_DEFAULT_CLUSTERS == 4


def test_churn_threshold_days() -> None:
    """CHURN_RECENCY_THRESHOLD_DAYS 기본값 확인."""
    s = Settings()
    assert s.CHURN_RECENCY_THRESHOLD_DAYS == 90
