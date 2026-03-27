"""ga-server(ga-nginx) 전용 — `lis.*` HTTPS 블록의 FastAPI·Dify 업스트림을 교체한다.

정본: docs/plans/lis_public_url_path_map.md §2.1
  • /api/v1/ · /health · /docs · /openapi.json · /ide/ 는 **반드시 동일 FASTAPI_UPSTREAM**.
  • Dify(/apps 등)는 **별도** DIFY_UPSTREAM.

패턴 B(로컬 우회·터널): SSH -R 등으로 ga-server **호스트**의 포트에 로컬 uvicorn 이 붙는 경우.
  • ga-nginx 가 **Docker** 이면 proxy_pass 의 127.0.0.1 은 «컨테이너 자신»이므로,
    호스트의 터널 포트로 가려면 **컨테이너 기본 게이트웨이**(compose 브리지) IP를 쓴다.
  • **실측(필수)**: `docker exec ga-nginx ip route show default` → `via X.X.X.X` 가 터널 끝점.
    예: docker0 만 쓰면 **172.17.0.1**, `ga-api-platform` 같은 사용자 네트워크면 **172.18.0.1** 등.
  • 터널 미가동 시 공인은 502 — §0 정상; `idr-fastapi` 로 되돌리는 것은 패턴 A(예외) 합의 시에만.

예외(패턴 A·별도 합의 시): FASTAPI_UPSTREAM = "http://idr-fastapi:8000"
  팀 운영 표준은 docs/plans/lis_public_url_path_map.md §0 (오직 로컬 우회).
"""

from pathlib import Path

# ── 여기만 환경에 맞게 수정 ─────────────────────────────────────────
# §0 표준: 로컬 uvicorn ← 터널(호스트 :8000 등) ← ga-nginx 는 **호스트 게이트웨이**로 접근
# ga-server(ga-api-platform 네트워크) 실측: default via 172.18.0.1 — 아래 기본값과 맞출 것
FASTAPI_UPSTREAM = "http://172.18.0.1:8000"
# (참고) docker0 전용 호스트면 172.17.0.1 일 수 있음 — 반드시 `ip route` 로 확인
# 예외(패턴 A): ga-server Docker API 컨테이너 — 합의·문서 있을 때만
# FASTAPI_UPSTREAM = "http://idr-fastapi:8000"

DIFY_UPSTREAM = "http://100.82.189.32:8080"
# ───────────────────────────────────────────────────────────────────

path = Path("/home/ubuntu/ga-api-platform/docs/nginx/go-almond.swagger.conf")
text = path.read_text()
marker_start = "server {\n    listen 443 ssl;\n    server_name lis.qk54r71z.freeddns.org;"
if marker_start not in text:
    raise SystemExit("marker not found")
idx = text.index(marker_start)
brace = 0
i = idx
while i < len(text):
    c = text[i]
    if c == "{":
        brace += 1
    elif c == "}":
        brace -= 1
        if brace == 0:
            end = i + 1
            break
    i += 1
else:
    raise SystemExit("no closing brace")

new_server = f"""server {{
    listen 443 ssl;
    server_name lis.qk54r71z.freeddns.org;

    ssl_certificate /etc/letsencrypt/live/go-almond.ddnsfree.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/go-almond.ddnsfree.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 80m;

    location /api/v1/ {{
        proxy_connect_timeout 10s;
        proxy_pass {FASTAPI_UPSTREAM}/api/v1/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }}

    location = /health {{
        proxy_pass {FASTAPI_UPSTREAM}/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location /docs {{
        proxy_pass {FASTAPI_UPSTREAM}/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location = /openapi.json {{
        proxy_pass {FASTAPI_UPSTREAM}/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    location = /ide {{
        return 301 /ide/;
    }}

    location /ide/ {{
        proxy_pass {FASTAPI_UPSTREAM}/ide/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }}

    location = / {{
        root /var/www/static/lis-demo;
        try_files /index.html =404;
    }}

    location / {{
        proxy_connect_timeout 10s;
        proxy_pass {DIFY_UPSTREAM};
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 3600s;
        proxy_buffering off;
    }}
}}"""

path.write_text(text[:idx] + new_server + text[end:])
print("patched bytes", idx, end)
print("FASTAPI_UPSTREAM=", FASTAPI_UPSTREAM)
print("DIFY_UPSTREAM=", DIFY_UPSTREAM)
