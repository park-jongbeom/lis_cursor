#!/usr/bin/env python3
"""ga-server — `lis.*` 블록의 `location = /` nginx 정적(root)을 FastAPI 프록시로 치환한다.

`go-almond.swagger.conf` 내 `server_name lis.qk54r71z.freeddns.org` 블록에서
`root /var/www/static/lis-demo` 형태만 대상으로 한다. (이미 프록시면 무시)

실행(ga-server):
  python3 infra/remote-proxy/patch_lis_root_to_fastapi_proxy.py
  docker restart ga-nginx   # 또는 호스트 nginx reload

업스트림은 `patch_lis_nginx_remote.py` 의 FASTAPI_UPSTREAM 과 동일 기본값.
"""

from __future__ import annotations

from pathlib import Path

CONF = Path("/home/ubuntu/ga-api-platform/docs/nginx/go-almond.swagger.conf")
FASTAPI_UPSTREAM = "http://172.18.0.1:8000"

OLD = """    location = / {
        root /var/www/static/lis-demo;
        try_files /index.html =404;
    }"""

NEW = f"""    location = / {{
        proxy_pass {FASTAPI_UPSTREAM}/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location = /index.html {{
        proxy_pass {FASTAPI_UPSTREAM}/index.html;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}"""


def main() -> None:
    t = CONF.read_text(encoding="utf-8")
    if OLD not in t:
        raise SystemExit(f"대상 블록 없음(이미 프록시이거나 경로 다름): {CONF}")
    CONF.write_text(t.replace(OLD, NEW, 1), encoding="utf-8")
    print("patched:", CONF)


if __name__ == "__main__":
    main()
