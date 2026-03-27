#!/usr/bin/env python3
"""로컬 강의 데모 동선 자체 검증 (T2 API 동등).

- `APP_ENV=development` 일 때만: `admin` 이 없으면 생성하고, 있으면 비밀번호를
  `LiveDemo2026!` 로 맞춘다(강의용 `demo/index.html` 자동 로그인과 동일).
- `POST /api/v1/auth/login` → `POST /api/v1/datasets/upload`(scm_sample.csv) → `GET …/profile`

사전: `make dev-up`, `make migrate`, FastAPI가 `BASE`(기본 http://127.0.0.1:8000)에서 수신 중이어야 한다.

실행 예: 리포 루트에서 `.env.dev` 로드 후 `ALLOWED_ORIGINS` JSON 배열 export,
`PYTHONPATH=idr_analytics poetry run python scripts/verify_demo_user_journey_local.py`
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

import httpx
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.user import User
from sqlalchemy import select

DEMO_USER = "admin"
DEMO_PASS = "LiveDemo2026!"


async def _sync_admin_demo_password() -> None:
    if settings.APP_ENV != "development":
        raise SystemExit("APP_ENV=development 필요 — admin 데모 비밀번호 동기화는 개발 전용")
    async with async_session_factory() as db:
        r = await db.execute(select(User).where(User.username == DEMO_USER))
        u = r.scalar_one_or_none()
        hp = hash_password(DEMO_PASS)
        if u is None:
            db.add(
                User(
                    id=uuid.uuid4(),
                    username=DEMO_USER,
                    hashed_password=hp,
                    role="admin",
                )
            )
            print(f"created user {DEMO_USER} (demo password)", file=sys.stderr)
        else:
            u.hashed_password = hp
            u.role = "admin"
            print("updated admin password to demo default (development only)", file=sys.stderr)
        await db.commit()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


async def _run(*, base: str) -> None:
    await _sync_admin_demo_password()
    base = base.rstrip("/")
    sample = _repo_root() / "demo" / "sample_data" / "scm_sample.csv"
    if not sample.is_file():
        msg = f"missing {sample}"
        raise SystemExit(msg)

    async with httpx.AsyncClient(base_url=base, timeout=60.0) as client:
        login = await client.post(
            "/api/v1/auth/login",
            data={"username": DEMO_USER, "password": DEMO_PASS},
        )
        if login.status_code != 200:
            raise SystemExit(f"login failed {login.status_code}: {login.text[:500]}")
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        files = {"file": ("scm_sample.csv", sample.read_bytes(), "text/csv")}
        data = {"dataset_name": "verify_demo_scm", "dataset_type": "scm"}
        up = await client.post("/api/v1/datasets/upload", files=files, data=data, headers=headers)
        if up.status_code != 201:
            raise SystemExit(f"upload failed {up.status_code}: {up.text[:500]}")
        body = up.json()
        ds_id = body["dataset_id"]
        assert body["row_count"] > 0

        prof = await client.get(f"/api/v1/datasets/{ds_id}/profile", headers=headers)
        if prof.status_code != 200:
            raise SystemExit(f"profile failed {prof.status_code}: {prof.text[:500]}")
        pj = prof.json()
        assert pj["dataset_name"] == "verify_demo_scm"

        ide = await client.get("/ide/docs/rules/")
        if ide.status_code != 200:
            raise SystemExit(f"/ide/docs/rules/ expected 200 got {ide.status_code}")

    print("OK: login → scm upload → profile → /ide/docs/rules/", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://127.0.0.1:8000", help="FastAPI root (no /api/v1)")
    args = p.parse_args()
    asyncio.run(_run(base=args.base))


if __name__ == "__main__":
    main()
