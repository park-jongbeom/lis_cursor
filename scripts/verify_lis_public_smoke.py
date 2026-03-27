#!/usr/bin/env python3
"""공인 `https://lis…` HTTP 스모크 — §0(로컬 uvicorn + 터널) 가동 시 검증.

- 루트 HTML, /health, /ide/docs/rules/
- JWT 로그인(기본 admin / LiveDemo2026! — 환경변수로 덮어쓰기)
- 샘플 카탈로그, upload-sample(scm_from_lis), GET /scm/restock-alert compact

에이전트(Tier2·Dify)는 `DIFY_API_BASE_URL` 이 강의 PC에서 맞게 잡혀 있지 않으면 502가 나므로
기본은 생략하고, `--with-agent` 시 dataset_id 를 직전 업로드 결과로 호출한다.

실행 예::

  python3 scripts/verify_lis_public_smoke.py
  python3 scripts/verify_lis_public_smoke.py --base https://lis.qk54r71z.freeddns.org
  LIS_VERIFY_PASSWORD='…' python3 scripts/verify_lis_public_smoke.py --with-agent
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx


def _fail(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    p = argparse.ArgumentParser(description="공인 lis.* 스모크 (터널·uvicorn 전제)")
    p.add_argument(
        "--base",
        default=os.environ.get("LIS_SMOKE_BASE", "https://lis.qk54r71z.freeddns.org"),
        help="사이트 오리진 (https://lis… , 슬래시 없음)",
    )
    p.add_argument("--user", default=os.environ.get("LIS_VERIFY_USER", "admin"))
    p.add_argument("--password", default=os.environ.get("LIS_VERIFY_PASSWORD", "LiveDemo2026!"))
    p.add_argument(
        "--insecure",
        action="store_true",
        help="TLS 검증 생략(자가서명·내부 CA 시)",
    )
    p.add_argument("--with-agent", action="store_true", help="마지막에 POST /api/v1/agent/query 시도")
    args = p.parse_args()

    base = args.base.rstrip("/")
    verify = not args.insecure

    with httpx.Client(timeout=60.0, verify=verify, follow_redirects=True) as client:
        r = client.get(base + "/")
        if r.status_code != 200 or "IDR Analytics" not in r.text:
            _fail(f"GET / expected 200 + 데모 제목, got {r.status_code}")

        r = client.get(base + "/health")
        if r.status_code != 200:
            _fail(f"GET /health expected 200, got {r.status_code}")
        try:
            hj = r.json()
        except Exception:
            _fail("/health body is not JSON")
        if hj.get("status") != "ok":
            _fail(f"/health JSON unexpected: {hj!r}")

        r = client.get(base + "/ide/docs/rules/")
        if r.status_code != 200:
            _fail(f"GET /ide/docs/rules/ expected 200, got {r.status_code}")

        login = client.post(
            base + "/api/v1/auth/login",
            data={"username": args.user, "password": args.password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if login.status_code != 200:
            _fail(f"login failed {login.status_code}: {login.text[:400]}")
        token = login.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        cat = client.get(base + "/api/v1/datasets/sample-catalog", headers=h)
        if cat.status_code != 200:
            _fail(f"sample-catalog failed {cat.status_code}: {cat.text[:400]}")
        catalog = cat.json()
        if not catalog:
            _fail("sample-catalog empty — demo/sample_data 및 SAMPLE_FILES 확인")
        names = {x["sample_file"] for x in catalog}
        pick = "scm_from_lis.csv" if "scm_from_lis.csv" in names else next(iter(names))

        up = client.post(
            base + "/api/v1/datasets/upload-sample",
            headers={**h, "Content-Type": "application/json"},
            json={"sample_file": pick, "dataset_type": "scm"},
        )
        if up.status_code != 201:
            _fail(f"upload-sample failed {up.status_code}: {up.text[:500]}")
        ds_id = up.json()["dataset_id"]

        restock = client.get(
            base + "/api/v1/scm/restock-alert",
            params={
                "dataset_id": ds_id,
                "target_column": "order_qty",
                "date_column": "order_date",
                "group_by": "test_code",
                "compact": "true",
            },
            headers=h,
        )
        if restock.status_code != 200:
            _fail(f"restock-alert failed {restock.status_code}: {restock.text[:500]}")

        if args.with_agent:
            ag = client.post(
                base + "/api/v1/agent/query",
                headers={**h, "Content-Type": "application/json"},
                json={
                    "query": "스모크 테스트 한 문장 요약",
                    "dataset_id": ds_id,
                    "query_type": 80,
                },
                timeout=180.0,
            )
            if ag.status_code != 200:
                _fail(
                    f"agent/query {ag.status_code}: {ag.text[:800]}\n"
                    "— Tier2: 강의 PC DIFY_*·uvicorn. Dify 404면 `verify_dify_upstream.py --dataset-id …`."
                )

    print("OK: / /health /ide/docs/rules/ login sample-catalog upload-sample restock-alert", file=sys.stderr)
    if args.with_agent:
        print("OK: agent/query", file=sys.stderr)


if __name__ == "__main__":
    main()
