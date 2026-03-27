"""ga-server(ga-nginx) 전용 — `lis.*` HTTPS 블록의 FastAPI·Dify 업스트림을 교체한다.

FastAPI: Docker DNS 이름 `idr-fastapi:8000` (`infra/deploy/public-edge` compose).
Dify: `DIFY_UPSTREAM`(Tailscale 등).
"""

from pathlib import Path

FASTAPI_UPSTREAM = "http://idr-fastapi:8000"
DIFY_UPSTREAM = "http://100.82.189.32:8080"

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
