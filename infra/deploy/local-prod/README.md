# 로컬 «운영형» 스택 (테스트용 인프라와 분리)

**IDR 백엔드·DB·Redis·(선택) Dify 는 전부 이 머신(local)에서 기동한다.** `https://lis.qk54r71z.freeddns.org/` 같은 공인 URL은 별도 역프록시(ga-nginx)가 **접속 경로만** 로컬로 넘기는 용도이며, [`../../remote-proxy/`](../../remote-proxy/) 문서·스니펫은 그 «URL 엣지」 전용이다.

| 구분 | Compose / 용도 |
|------|------------------|
| **테스트** | `docker-compose.test.yml` — `make test` 전용(PG 15433, Redis 6380), 격리 네트워크 |
| **일상 개발** | `docker-compose.dev.yml` — PG 15432, Redis 6379, 호스트 uvicorn `:8000` + 보통 `.env` |
| **운영형 로컬** | `docker-compose.prod.yml` — PG·Redis **볼륨·설정이 prod용**. 호스트에서 `APP_ENV=production` + `.env.prod` 로 uvicorn 실행 |

`dev` 와 `prod` compose 는 **동일한 컨테이너 이름**(`idr-postgres`, `idr-redis`)을 쓰므로 **동시에 띄우지 않는다.**

## 절차 요약

1. **`.env.prod`**: `cp env.prod.example .env.prod` 후 `SECRET_KEY`, `POSTGRES_PASSWORD`, `ALLOWED_ORIGINS`, `ANTHROPIC_API_KEY` / `DIFY_*` 등 설정.
2. **DB·Redis**: `make prod-up` (또는 `podman-compose -f docker-compose.prod.yml --env-file .env.prod up -d`).
3. **업로드 디렉터리**: `mkdir -p data/uploads`.
4. **마이그레이션**: `set -a && source .env.prod && set +a && make migrate-prod` (Makefile 목표) 또는 동일 내용을 수동 실행.
5. **admin 사용자**: `demo/README.md` 스니펫.
6. **API**: `set -a && source .env.prod && set +a && PYTHONPATH=idr_analytics poetry run uvicorn app.main:app --host 127.0.0.1 --port 8010`
   - **`/ide/docs/rules/`** (교육용 규칙 HTML)는 FastAPI `StaticFiles`로 위 uvicorn이 서빙한다. `main.py`·`demo/ide/`·`IDE_STATIC_ROOT` 를 바꾼 뒤에는 **uvicorn을 재시작**해야 공인 URL·9080 경유 요청에 반영된다.
   - `.env.prod`에 `IDE_STATIC_ROOT`(리포의 `demo/ide` 절대 경로)를 두면 자동 경로 탐색과 무관하게 고정할 수 있다(`env.prod.example` 주석 참고).
   - 기동 확인: `make prod-smoke-ide` (8010이 떠 있을 때 HTTP 코드 출력).
7. **한 URL로 데모+API+교육 `/ide/`**(선택): `nginx-local-demo.conf` 를 시스템 nginx 에 넣거나, 포함 경로만 맞춰 `sudo cp` 후 reload. 브라우저에서 **`http://127.0.0.1:9080/`** — JWT 로그인(`demo/index.html`) 후 사용. API 베이스는 자동으로 `http://127.0.0.1:9080/api/v1`. **`/ide/`** 는 동일 파일의 `location /ide/` → **8010 uvicorn** 프록시( **`/api/v1/` 과 같은 FastAPI** ). 공인 `lis.*` 에서의 **`/`·`/apps`·`/ide/`** 역할 표·재구축 순서는 **`docs/plans/lis_public_url_path_map.md`** §6. (참고: 9080 스택에는 Dify **`/apps`** 가 없을 수 있음 — 로컬은 데모+API+`/ide` 검증용.)
8. **ARQ**(SCM/CRM 잡): 별도 터미널에서 `set -a && source .env.prod && set +a && PYTHONPATH=idr_analytics poetry run arq app.workers.arq_worker.WorkerSettings`.

## systemd (선택)

장시간 로컬 상시 기동 시 `idr-analytics.service.example` 의 `User`·`WorkingDirectory`·`ExecStart` 의 poetry 경로를 본인 환경에 맞게 수정해 `/etc/systemd/system/` 에 설치한다.
