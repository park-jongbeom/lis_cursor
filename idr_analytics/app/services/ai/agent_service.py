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
            raw: Any = None
            first_scalar: Any = None
            for key in ("answer", "output", "text", "result", "summary"):
                cand = outputs.get(key)
                if isinstance(cand, str) and cand.strip():
                    raw = cand
                    break
                if first_scalar is None and cand is not None and not isinstance(cand, (dict, list)):
                    first_scalar = cand
            if raw is None and outputs:
                # 키가 고정되지 않은 워크플로를 위해 첫 스칼라 출력값을 보조 답변으로 사용
                for _, v in outputs.items():
                    if isinstance(v, str) and v.strip():
                        raw = v
                        break
                    if first_scalar is None and v is not None and not isinstance(v, (dict, list)):
                        first_scalar = v
            if raw is None and first_scalar is not None:
                raw = first_scalar
            if isinstance(raw, str):
                answer = raw
            elif raw is None:
                answer = ""
            else:
                answer = str(raw)

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
        workflow_data = data.get("data", {})
        wf_status = workflow_data.get("status") if isinstance(workflow_data, dict) else None
        wf_error = workflow_data.get("error") if isinstance(workflow_data, dict) else None
        if wf_run is not None or outputs or wf_status is not None:
            supporting = {
                "workflow_run_id": wf_run,
                "outputs": outputs,
                "workflow_status": wf_status,
                "workflow_error": wf_error,
            }

        if not answer:
            if wf_run is not None:
                answer = "Dify 워크플로 실행은 완료되었지만 출력 텍스트가 비어 있습니다. " f"workflow_run_id={wf_run}"
            else:
                answer = "Dify 워크플로가 빈 응답을 반환했습니다."

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
