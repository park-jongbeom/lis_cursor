# 공인 `lis.*` · Tier2(Dify) · 로컬 uvicorn — 문제 진단·수정 가이드

> **목적**: `POST /api/v1/agent/query` 502, Dify `workflows/run` 401/404, nginx HTML 400, `.env` 키 “사라짐” 혼동, 로컬 운영(8000/8010) 재기동 등 **동일 증상 재발 시 바로 조치**할 수 있도록 절차를 한곳에 모은다.  
> **정본(경로·운영 원칙)**: `docs/plans/lis_public_url_path_map.md` · `docs/rules/project_context.md`(ga-server·공인 URL) · `infra/dify/workflows/README.md`

---

## 1. 증상 매트릭스 (먼저 여기서 분기)

| 증상 | 의미 (대개) | 점검 절차 |
|------|-------------|-----------|
| 공인에서 **GET** `/api/v1/bi/regional-heatmap` 등은 **200**, **POST** `/api/v1/agent/query` 만 **502** | Tier1(FastAPI만)은 정상, **Tier2가 Dify를 호출하다 실패**해 앱이 502로 감쌈 | [2절](#2-post-apiv1agentquery-502-브라우저) |
| 브라우저 502인데 **응답 본문이 JSON** (`detail.code` 가 `DIFY_HTTP_ERROR`, `DIFY_REQUEST_ERROR` 등) | **엣지 nginx 단절이 아니라** uvicorn이 Dify 오류를 HTTP 502로 매핑한 것 | [2절](#2-post-apiv1agentquery-502-브라우저), [3절](#3-dify_api_base_url--workflow_id--api-키) |
| `curl …/v1/workflows/run` → **401** | Dify가 **API 키 미인정** (키 누락·오타·플레이스홀터 그대로 입력·다른 앱 키) | [3.3절](#33-dify_api_key-401) |
| `curl …/v1/workflows/run` → **HTML** `400 Bad Request` + `nginx/…` | **요청이 깨짐**(셸 줄바꿈·따옴표·`url`/`curl` 오타) 또는 HTTP/2 이슈 | [3.4절](#34-curl로-v1workflowsrun-검증할-때) |
| `workflows/run` 은 **200**인데 `data.status` 가 **failed**, `error` 에 **404** | 워크플로 **내부 HTTP 노드**가 FastAPI를 호출했다가 404 (dataset/period/컬럼 불일치) | [4절](#4-tier2-워크플로-failed--http-404) |
| 로컬 **8010** 로그인 **500** `InvalidPasswordError` for user `idr` | **`.env.prod`의 `DATABASE_URL` 비밀번호**가 실제 `idr-postgres` 컨테이너와 불일치 | [5.2절](#52-로컬-운영형-8010--envprod) |
| **8000** uvicorn 기동 직후 **SettingsError** / `ALLOWED_ORIGINS` 파싱 오류 | 셸에 **export된 `ALLOWED_ORIGINS`** 가 잘못되었거나, `source .env` 로 JSON이 깨짐 | [5.1절](#51-개발-8000--env) |

---

## 2. `POST /api/v1/agent/query` 502 (브라우저)

1. 개발자 도구 **Network → 해당 요청 → Response** 에서 본문 확인.
2. JSON이고 `detail.code` 가 `DIFY_HTTP_ERROR` 이고 `status_code` 가 **404** 이면 → Dify Open API URL/경로 또는 `workflow_id` 문제 가능성이 큼 ([3절](#3-dify_api_base_url--workflow_id--api-키)).
3. `DIFY_REQUEST_ERROR` / 타임아웃 힌트면 → **uvicorn이 도는 PC**에서 `DIFY_API_BASE_URL` 로 `curl` 이 안 되는 경우가 많음.

**코드 근거**: `idr_analytics/app/api/v1/endpoints/agent.py` 에서 Dify `httpx` 오류 시 `502` 로 올림.

---

## 3. `DIFY_API_BASE_URL` · `workflow_id` · API 키

### 3.1 베이스 URL

- **형식**: `http(s)://호스트:포트/v1` (**반드시 `/v1`까지**). `AgentService`는 `{베이스}/workflows/run` 으로 POST 한다.
- **기준 머신**: 브라우저가 아니라 **uvicorn 프로세스가 돌아가는 호스트**에서 도달 가능한 주소여야 한다 (`env.example` 주석과 동일).
- 공인 호스트 뒤에 Dify API가 붙어 있으면 `https://lis.…/v1` 형태도 가능(그 PC에서 `curl`로 검증).

### 3.2 `DIFY_WORKFLOW_ID`

- **API에 넣는 값은 UUID** (Studio **API 접근**에서 확인). 앱 **표시 이름**(예: `IDR CRM·BI Tier2`)을 그대로 넣으면 404 등으로 깨지기 쉽다.
- **단일 워크플로 전용 API 키**만 쓰는 경우 비워도 된다 (`env.example` · `infra/dify/workflows/README.md`).

### 3.3 `DIFY_API_KEY` (401)

- **Git에 올라가는 `env.example` / `env.prod.example`** 는 `app-xxxxxxxx…` **플레이스홀더**다. “키가 사라졌다”고 느끼는 경우 **실제 값은 `.env` / `.env.prod` / `infra/dify/.env`** 에만 둔다.
- 문서·예시에 적었던 `<DIFY_API_KEY>` 를 **그대로** 넣으면 항상 401에 가깝다. Studio에서 발급한 `app-…` 를 사용한다.
- 키가 채팅·로그에 노출되면 **재발급** 권장.

### 3.4 `curl`로 `/v1/workflows/run` 검증할 때

- **한 줄**로 실행한다 (백슬래시 줄 연속이 깨지면 `Could not resolve host: curl` 등 이상 증상).
- 명령은 **`curl`** (오타 `url` 금지).
- 응답이 **HTML** 이고 nginx **400** 이면, 본문 JSON이 아니라 **클라이언트 요청 형식 문제**를 의심한다. 필요 시 `curl --http1.1` 사용.
- 워크플로 입력에 `dataset_id` 등이 필수면 본문 `inputs`에 포함해야 **401/404가 아닌** 다음 단계(400 JSON 등)로 진행된다.

**자동 재현(리포 루트)**:

```bash
poetry run python scripts/verify_dify_upstream.py --dataset-id '<UUID>' --period 'YYYY-MM'
# 로컬 운영형 DIFY_* 만 쓰려면:
poetry run python scripts/verify_dify_upstream.py --env-file .env.prod --dataset-id '<UUID>' --period 'YYYY-MM'
```

---

## 4. Tier2 워크플로 `failed` · HTTP 404

- DSL이 CRM·BI 노드를 모두 치는 경우 **`mixed_from_lis.csv`** 업로드 데이터셋과, CSV에 실제 존재하는 **`period`** 값을 맞출 것 (`infra/dify/workflows/README.md` 표).
- `dataset_id` 를 placeholder 로 두면 내부 HTTP 노드가 FastAPI에서 **404**를 받기 쉽다.

---

## 5. 로컬 uvicorn 재기동 (설정 반영)

### 5.1 개발 **8000** + `.env`

- Pydantic은 리포 루트의 **`.env`** 를 읽는다 (`idr_analytics/app/core/config.py`). 작업 디렉터리는 **프로젝트 루트**여야 한다.
- 셸에 **`export ALLOWED_ORIGINS=...`** 가 잘못 잡혀 있으면 `.env`보다 우선되어 **파싱 오류**가 난다. 기동 전에 `unset ALLOWED_ORIGINS` 후 실행하거나, export 값을 올바른 JSON 배열 문자열로 맞춘다.
- **`set -a && source .env`** 는 `ALLOWED_ORIGINS` 같은 JSON 줄을 셸이 깨뜨릴 수 있어 **권장하지 않는다** (8000 기준).

예시:

```bash
cd /path/to/lis_cursor
unset ALLOWED_ORIGINS   # 잘못된 export가 있을 때만
PYTHONPATH=idr_analytics poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 5.2 로컬 운영형 **8010** + `.env.prod`

- `infra/deploy/local-prod/README.md` 절차: `source .env.prod` 후 동일하게 uvicorn, 포트 **8010**.
- **`make dev-up` 과 동일한 `idr-postgres`를 쓰는 경우** `.env.prod`의 `POSTGRES_PASSWORD` / `DATABASE_URL` 이 **실제 컨테이너 비밀번호**와 일치해야 로그인 시 DB 연결이 된다.

### 5.3 공인 URL 반영

- 엣지 nginx는 **터널이 붙은 포트**(보통 **8000**)를 본다. `DIFY_*`·코드 변경 후에는 해당 uvicorn을 **재시작**한다.
- `/ide`·데모 정적: `make prod-smoke-ide` (8010) 또는 `GET /ide/docs/rules/` 로 확인.

---

## 6. 엣지 nginx 타임아웃

- `infra/remote-proxy/ga-server-append-lis.qk54r71z.conf.snippet` 의 `location /api/v1/` 에 `proxy_read_timeout` 이 있으면, **즉시 뜨는 JSON 502**는 대개 타임아웃보다 **Dify 4xx/연결 실패** 쪽을 먼저 본다.

---

## 7. 관련 스크립트·문서

| 항목 | 경로 |
|------|------|
| 공인 HTTP 스모크 (로그인·샘플·선택 Tier2) | `scripts/verify_lis_public_smoke.py` (`--with-agent`) |
| Dify `workflows/run` 동형 호출 | `scripts/verify_dify_upstream.py` |
| 워크플로·`.env` 매핑 | `infra/dify/workflows/README.md` |
| 로컬 운영형 스택 | `infra/deploy/local-prod/README.md` |
| 엣지 스니펫 | `infra/remote-proxy/ga-server-append-lis.qk54r71z.conf.snippet` |

---

## 8. 변경 이력 (요약)

| 시기 | 내용 |
|------|------|
| 2026-03-28 | 초안: 공인 agent 502 vs Tier1 200, Dify UUID·키·curl·uvicorn 8000/8010·DB 비밀번호 정합 |
