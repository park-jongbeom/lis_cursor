"""Dify Workflow 프록시 — HTTP만, Pandas/DB 대량 연산 금지."""

from __future__ import annotations

import time
import uuid
from typing import Any, cast

import httpx

from app.core.config import settings
from app.schemas.agent import AgentQueryResponse


class AgentService:
    async def analyze(
        self,
        query: str,
        dataset_id: uuid.UUID | None,
        session_id: uuid.UUID | None,
        extra_inputs: dict[str, str] | None = None,
    ) -> AgentQueryResponse:
        t0 = time.perf_counter()
        base = settings.DIFY_API_BASE_URL.rstrip("/")
        url = f"{base}/workflows/run"
        inputs: dict[str, str] = {"user_query": query}
        if dataset_id is not None:
            inputs["dataset_id"] = str(dataset_id)
        if session_id is not None:
            inputs["session_id"] = str(session_id)
        if extra_inputs:
            inputs.update(extra_inputs)
        payload: dict[str, Any] = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": str(session_id) if session_id is not None else "internal-agent",
        }
        if settings.DIFY_WORKFLOW_ID:
            payload["workflow_id"] = settings.DIFY_WORKFLOW_ID

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {settings.DIFY_API_KEY}"},
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = cast(dict[str, Any], response.json())

        # Dify 문서 예시: data["data"]["outputs"]["answer"] — 버전별로 상이할 수 있음 (Gate B 매핑)
        outputs = data.get("data", {}).get("outputs", {}) if isinstance(data.get("data"), dict) else {}
        answer = ""
        if isinstance(outputs, dict):
            raw = outputs.get("answer")
            if raw is None:
                raw = outputs.get("output")
            answer = raw if isinstance(raw, str) else str(raw or "")

        out_sid = session_id or uuid.uuid4()
        meta = data.get("metadata") or data.get("data", {}).get("metadata", {})
        llm_model: str | None = None
        if isinstance(meta, dict):
            m = meta.get("model") or meta.get("llm_model")
            llm_model = str(m) if m is not None else None
        if llm_model is None:
            llm_model = settings.LLM_MODEL

        wf_run = data.get("workflow_run_id") or data.get("id")
        supporting: dict[str, Any] | None = None
        if wf_run is not None or outputs:
            supporting = {"workflow_run_id": wf_run, "outputs": outputs}

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return AgentQueryResponse(
            session_id=out_sid,
            query=query,
            answer=answer,
            supporting_data=supporting,
            route_used="ai_tier2",
            llm_model=llm_model,
            processing_time_ms=elapsed_ms,
        )


agent_service = AgentService()
