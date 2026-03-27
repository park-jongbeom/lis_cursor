"""Agent endpoint Dify 에러 분류 단위 테스트."""

from __future__ import annotations

import json

import httpx
from app.api.v1.endpoints.agent import _build_dify_http_error_detail


def _http_status_error(status_code: int, payload: dict[str, str] | None = None) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "http://localhost:8080/v1/workflows/run")
    if payload is None:
        response = httpx.Response(status_code=status_code, request=request, text="upstream error")
    else:
        response = httpx.Response(
            status_code=status_code,
            request=request,
            content=json.dumps(payload).encode("utf-8"),
            headers={"content-type": "application/json"},
        )
    return httpx.HTTPStatusError("upstream error", request=request, response=response)


def test_build_dify_http_error_detail_input_error() -> None:
    err = _http_status_error(400, {"code": "invalid_param", "message": "period is required"})
    detail = _build_dify_http_error_detail(err)
    assert detail["code"] == "DIFY_INPUT_ERROR"
    assert detail["status_code"] == 400


def test_build_dify_http_error_detail_auth_error() -> None:
    err = _http_status_error(401, {"code": "unauthorized", "message": "invalid api key"})
    detail = _build_dify_http_error_detail(err)
    assert detail["code"] == "DIFY_AUTH_ERROR"
    assert detail["status_code"] == 401


def test_build_dify_http_error_detail_404_adds_hint() -> None:
    request = httpx.Request("POST", "http://localhost:8080/v1/workflows/run")
    response = httpx.Response(
        status_code=404,
        request=request,
        text="404 page not found\n",
    )
    err = httpx.HTTPStatusError("not found", request=request, response=response)
    detail = _build_dify_http_error_detail(err)
    assert detail["code"] == "DIFY_HTTP_ERROR"
    assert detail["status_code"] == 404
    assert "hint" in detail
    assert "DIFY_API_BASE_URL" in detail["hint"]
