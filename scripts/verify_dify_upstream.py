#!/usr/bin/env python3
"""uvicorn과 동일한 방식으로 Dify `POST …/workflows/run` 을 호출해 Tier2 업스트림을 진단한다.

`AgentService`와 동일 URL·헤더·본문 형태. **설정은 `.env`의 `DIFY_API_BASE_URL`·`DIFY_API_KEY`·
`DIFY_WORKFLOW_ID` 만** 쓴다(앱 구성).

**`dataset_id`는 브라우저에서 샘플 업로드 후 표시되는 값처럼 매번 달라지므로**, 고정 환경변수가
아니라 **`--dataset-id` 인자로 넘기는 것이 정상**이다. `--period`도 CSV에 맞게 인자로 지정한다.

  poetry run python scripts/verify_dify_upstream.py --dataset-id <UUID> [--period 2024-01]

CI 등에서만 선택적으로 `DIFY_VERIFY_DATASET_ID` / `DIFY_VERIFY_PERIOD` 환경변수 폴백을 쓸 수 있다
(인자가 있으면 인자가 우선).

성공 시 workflow 응답 일부를 출력. 404·401은 `infra/dify/workflows/README.md` 참고.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key.startswith("DIFY_"):
            continue
        val = val.strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        os.environ.setdefault(key, val)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dify workflows/run 업스트림 스모크 (FastAPI와 동일 요청 형식)")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="이 파일에서 DIFY_* 키를 읽어 기본값으로 설정(이미 export된 값은 덮어쓰지 않음)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="HTTP 타임아웃(초)",
    )
    parser.add_argument(
        "--dataset-id",
        default="",
        metavar="UUID",
        help="워크플로 dataset_id(데모/API에서 복사). 생략 시 placeholder로 HTTP 노드 실패 가능",
    )
    parser.add_argument(
        "--period",
        default="",
        metavar="YYYY-MM",
        help="regional-heatmap용 period(해당 CSV period 컬럼 값과 동일). 미지정 시 2024-01",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)
    _load_env_file(args.env_file if args.env_file.is_absolute() else repo_root / args.env_file)

    base = os.environ.get("DIFY_API_BASE_URL", "").strip().rstrip("/")
    api_key = os.environ.get("DIFY_API_KEY", "").strip()
    workflow_id = os.environ.get("DIFY_WORKFLOW_ID", "").strip()

    if not base:
        print("DIFY_API_BASE_URL 이 비어 있습니다.", file=sys.stderr)
        sys.exit(2)
    if not api_key:
        print("DIFY_API_KEY 가 비어 있습니다.", file=sys.stderr)
        sys.exit(2)

    url = f"{base}/workflows/run"
    # 인자 우선 → CI용 env 폴백 → dataset_id 기본은 placeholder
    dataset_id = (args.dataset_id or os.environ.get("DIFY_VERIFY_DATASET_ID", "")).strip()
    if not dataset_id:
        dataset_id = "00000000-0000-4000-8000-000000000000"
    period = (args.period or os.environ.get("DIFY_VERIFY_PERIOD", "") or "2024-01").strip() or "2024-01"
    payload: dict[str, Any] = {
        "inputs": {
            "user_query": "upstream-smoke: ping",
            "period": period,
            "dataset_id": dataset_id,
        },
        "response_mode": "blocking",
        "user": "verify-dify-upstream",
    }
    if workflow_id:
        payload["workflow_id"] = workflow_id

    print("POST", url, file=sys.stderr)
    print("workflow_id in body:", workflow_id or "(생략 — API 키에 묶인 단일 앱)", file=sys.stderr)
    print("inputs.dataset_id:", dataset_id, file=sys.stderr)
    print("inputs.period:", period, file=sys.stderr)
    if dataset_id == "00000000-0000-4000-8000-000000000000":
        print(
            "(dataset_id 미지정 — placeholder. 실제 검증: "
            "`--dataset-id <데모 업로드 후 current dataset_id 또는 API 목록의 id>`)",
            file=sys.stderr,
        )

    try:
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=args.timeout,
        )
    except httpx.RequestError as exc:
        print(f"연결 실패: {exc}", file=sys.stderr)
        sys.exit(3)

    text = resp.text
    snippet = text[:1200] + ("…" if len(text) > 1200 else "")
    print(f"HTTP {resp.status_code}", file=sys.stderr)
    if resp.status_code >= 400:
        print(snippet, file=sys.stderr)
        sys.exit(4)

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("본문이 JSON이 아님:", file=sys.stderr)
        print(snippet, file=sys.stderr)
        sys.exit(5)

    print(json.dumps(data, ensure_ascii=False, indent=2)[:8000])

    wd = data.get("data") if isinstance(data.get("data"), dict) else {}
    if wd.get("status") == "failed":
        print("", file=sys.stderr)
        print(
            "워크플로 status=failed — HTTP 노드가 받은 404/기타 오류일 수 있음. 점검:",
            file=sys.stderr,
        )
        print(
            "  • BI: `period` 가 해당 CSV `period` 컬럼 값과 일치하는지 (`--period 2024-02` 등).",
            file=sys.stderr,
        )
        print(
            "  • CRM: churn-risk 는 customer_code, order_date, order_amount 컬럼 필요 — "
            "SCM-only 업로드면 404. Tier2 검증은 `mixed_from_lis.csv` 업로드 데이터셋을 권장.",
            file=sys.stderr,
        )
        print("  • Dify Studio 추적으로 실패한 HTTP 노드 URL·응답 본문 확인.", file=sys.stderr)


if __name__ == "__main__":
    main()
