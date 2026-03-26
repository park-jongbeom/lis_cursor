#!/usr/bin/env python3
"""FastAPI `POST /api/v1/auth/login` 호출 후 access_token 출력.

Dify 워크플로 HTTP 요청 노드의 `Authorization: Bearer ...` 값으로 사용합니다.
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="IDR FastAPI 로그인 JWT 발급")
    parser.add_argument(
        "--bearer",
        action="store_true",
        help="Authorization 헤더 한 줄 전체 출력 (Dify 붙여넣기용)",
    )
    args = parser.parse_args()

    base = os.environ.get("IDR_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    username = os.environ.get("IDR_LOGIN_USERNAME", "").strip()
    password = os.environ.get("IDR_LOGIN_PASSWORD", "")

    if not username or not password:
        print(
            "IDR_LOGIN_USERNAME, IDR_LOGIN_PASSWORD 환경 변수가 필요합니다.\n"
            "예: IDR_LOGIN_USERNAME=alice IDR_LOGIN_PASSWORD='secret' poetry run python ...\n"
            "또는 .env 에 동일 키를 넣은 뒤: export $(grep -E '^IDR_' .env | xargs)",
            file=sys.stderr,
        )
        sys.exit(1)

    url = f"{base}/api/v1/auth/login"
    try:
        resp = httpx.post(
            url,
            data={"username": username, "password": password},
            timeout=30.0,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"HTTP {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"요청 실패 ({url}): {e}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    token = data.get("access_token")
    if not token:
        print("응답에 access_token 없음", file=sys.stderr)
        sys.exit(1)

    if args.bearer:
        print(f"Authorization: Bearer {token}")
    else:
        print(token)


if __name__ == "__main__":
    main()
