"""AgentService 단위 테스트 — httpx mock."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.schemas.agent import AgentQueryResponse
from app.services.ai.agent_service import agent_service


def _dify_response(answer: str = "분석 결과입니다.") -> dict:
    return {
        "workflow_run_id": "wf-abc123",
        "data": {
            "outputs": {"answer": answer},
            "metadata": {"model": "claude-sonnet-4-6"},
        },
    }


def _mock_httpx_post(response_data: dict, status_code: int = 200) -> AsyncMock:
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = response_data
    if status_code >= 400:
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "error", request=MagicMock(), response=mock_response
        )
    else:
        mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)
    return mock_client


# ── 정상 케이스 ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyze_returns_response() -> None:
    """A-01: 정상 Dify 응답 → AgentQueryResponse 반환, answer 매핑."""
    mock_client = _mock_httpx_post(_dify_response("결과입니다"))

    with patch("app.services.ai.agent_service.httpx.AsyncClient", return_value=mock_client):
        result = await agent_service.analyze("이탈 고객 분석", None, None)

    assert isinstance(result, AgentQueryResponse)
    assert result.answer == "결과입니다"


@pytest.mark.asyncio
async def test_analyze_maps_output_field_to_answer() -> None:
    """Dify가 outputs.output만 줄 때도 answer로 매핑."""
    mock_client = _mock_httpx_post(
        {
            "workflow_run_id": "wf-abc123",
            "data": {
                "outputs": {"output": "output 기반 응답"},
                "metadata": {"model": "claude-sonnet-4-6"},
            },
        }
    )

    with patch("app.services.ai.agent_service.httpx.AsyncClient", return_value=mock_client):
        result = await agent_service.analyze("이탈 고객 분석", None, None)

    assert result.answer == "output 기반 응답"


@pytest.mark.asyncio
async def test_analyze_without_dataset_id() -> None:
    """A-02: dataset_id=None → inputs에 dataset_id 키 없음."""
    captured_payload: dict = {}

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = _dify_response()
    mock_response.raise_for_status.return_value = None

    async def _fake_post(url: str, **kwargs: object) -> object:
        captured_payload.update(kwargs.get("json", {}))  # type: ignore[arg-type]
        return mock_response

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=_fake_post)

    with patch("app.services.ai.agent_service.httpx.AsyncClient", return_value=mock_client):
        await agent_service.analyze("쿼리", None, None)

    inputs = captured_payload.get("inputs", {})
    assert "dataset_id" not in inputs


@pytest.mark.asyncio
async def test_analyze_includes_user_and_extra_inputs() -> None:
    """payload에 user와 extra input(period) 포함."""
    captured_payload: dict = {}
    sid = uuid.uuid4()

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = _dify_response("ok")
    mock_response.raise_for_status.return_value = None

    async def _fake_post(url: str, **kwargs: object) -> object:
        _ = url
        captured_payload.update(kwargs.get("json", {}))  # type: ignore[arg-type]
        return mock_response

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(side_effect=_fake_post)

    with patch("app.services.ai.agent_service.httpx.AsyncClient", return_value=mock_client):
        await agent_service.analyze("쿼리", None, sid, extra_inputs={"period": "2025-Q4"})

    assert captured_payload.get("user") == str(sid)
    assert captured_payload.get("inputs", {}).get("period") == "2025-Q4"


@pytest.mark.asyncio
async def test_analyze_session_id_auto_generated() -> None:
    """A-03: session_id=None → UUID 자동 생성."""
    mock_client = _mock_httpx_post(_dify_response())

    with patch("app.services.ai.agent_service.httpx.AsyncClient", return_value=mock_client):
        result = await agent_service.analyze("쿼리", None, None)

    assert isinstance(result.session_id, uuid.UUID)


@pytest.mark.asyncio
async def test_analyze_with_session_id() -> None:
    """A-03b: session_id 전달 → 그대로 반환."""
    mock_client = _mock_httpx_post(_dify_response())
    sid = uuid.uuid4()

    with patch("app.services.ai.agent_service.httpx.AsyncClient", return_value=mock_client):
        result = await agent_service.analyze("쿼리", None, sid)

    assert result.session_id == sid


@pytest.mark.asyncio
async def test_analyze_route_used_ai_tier2() -> None:
    """A-05: route_used 항상 'ai_tier2'."""
    mock_client = _mock_httpx_post(_dify_response())

    with patch("app.services.ai.agent_service.httpx.AsyncClient", return_value=mock_client):
        result = await agent_service.analyze("쿼리", None, None)

    assert result.route_used == "ai_tier2"


@pytest.mark.asyncio
async def test_analyze_processing_time_ms_is_int() -> None:
    """A-06: processing_time_ms 존재하고 int 타입."""
    mock_client = _mock_httpx_post(_dify_response())

    with patch("app.services.ai.agent_service.httpx.AsyncClient", return_value=mock_client):
        result = await agent_service.analyze("쿼리", None, None)

    assert isinstance(result.processing_time_ms, int)
    assert result.processing_time_ms >= 0


# ── 오류 케이스 ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyze_http_error_propagates() -> None:
    """A-04: HTTP 4xx → httpx.HTTPStatusError 전파."""
    mock_client = _mock_httpx_post({}, status_code=401)

    with patch("app.services.ai.agent_service.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(httpx.HTTPStatusError):
            await agent_service.analyze("쿼리", None, None)


# ── 필요한 MagicMock import ────────────────────────────────────────────────────
from unittest.mock import MagicMock  # noqa: E402
