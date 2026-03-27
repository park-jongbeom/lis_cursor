# Dify Workflow DSL (IDR)

## 파일

| 파일 | 설명 |
|------|------|
| [`idr_crm_bi_tier2.yml`](idr_crm_bi_tier2.yml) | CRM `churn-risk` + BI `regional-heatmap` (둘 다 `compact=true`) → 변수 집계자 → LLM → 종료 |

흐름·엔드포인트 근거: [`docs/rules/dify_integration.md`](../../../docs/rules/dify_integration.md) §3.2.

## FastAPI `.env` 와 맞출 값

| 변수 | 요약 |
|------|------|
| **`DIFY_API_BASE_URL`** | FastAPI(uvicorn) **프로세스가 실행되는 머신**에서 Dify Open API에 도달하는 주소 + `/v1` (예: 강의 PC에서 Dify가 루프백이면 `http://127.0.0.1:8080/v1`). 브라우저 URL과 혼동하지 말 것. |
| **`DIFY_WORKFLOW_ID`** | 워크플로 **UUID만** 유효. 앱 제목·한글 이름 등 문자열을 넣으면 Dify가 엉뚱한 경로로 가 Tier2가 실패함. Studio **API 접근** 또는 `POST /v1/workflows/run` 응답의 `data.workflow_id` 로 확인. **단일 워크플로 전용 API 키**면 비워도 됨(`AgentService`가 `workflow_id` 필드를 생략). |
| **`DIFY_API_KEY`** | 해당 앱의 API Key. |

템플릿: 루트 [`env.example`](../../../env.example) · 운영형 [`env.prod.example`](../../../env.prod.example).

### `workflows/run` 은 200인데 노드에서 `401`

Dify **내부** HTTP Request 노드가 FastAPI를 부를 때 `Authorization: Bearer <JWT>` 가 없거나 만료된 경우입니다.

1. 프로젝트 루트 `.env` 에 `IDR_LOGIN_USERNAME` / `IDR_LOGIN_PASSWORD`(및 필요 시 `IDR_API_BASE_URL`) 설정.
2. `make dify-fastapi-jwt-bearer` 또는 `poetry run python infra/dify/scripts/fetch_fastapi_jwt.py --bearer` 로 한 줄 발급 → Dify Studio에서 해당 노드 헤더에 붙여넣기(또는 Secret·환경변수로 참조). 상세는 아래 「가져온 직후 필수 수정」.
3. **uvicorn 재시작** 후 공인/로컬에서 Tier2를 다시 호출.

### `workflows/run` 이 **404** (`404 page not found` 등)

FastAPI `AgentService`는 **`{DIFY_API_BASE_URL}/workflows/run`** 으로 POST 합니다. 베이스는 반드시 **`/v1`까지** 포함합니다(예: `http://127.0.0.1:8080/v1`).

| 원인 | 조치 |
|------|------|
| 베이스 URL 오타·누락 | `/apps`·`/console` 주소와 혼동하지 말 것. API는 nginx 뒤 **`/v1`** 경로. |
| Dify가 원격만 있음 | **uvicorn이 도는 PC**에서 `curl`로 열리는 호스트로 `DIFY_API_BASE_URL` 설정. |
| 잘못된 `workflow_id` | 본문에 넣는 UUID가 앱·게시본과 불일치하면 404가 날 수 있음 — Studio **API 접근**에서 다시 확인. |
| 로컬에 Dify 없음 | `http://127.0.0.1:8080/v1` 은 **같은 머신에** `make dify-up` 등으로 Dify가 떠 있을 때만 유효. |

**진단**: 프로젝트 루트에서 `AgentService`와 동일한 `POST …/workflows/run` 을 재현합니다.

```bash
poetry run python scripts/verify_dify_upstream.py --dataset-id <UUID> [--period 2024-01]
# 또는
make verify-dify-upstream ARGS='--dataset-id <UUID> --period 2024-01'
```

`dataset_id`·`period` 는 **브라우저 데모에서 업로드 직후 표시되는 값 / CSV에 실제 있는 기간**처럼 매번 달라지므로 **CLI 인자**로 넘기는 것이 맞고, `.env`에 고정해 두지 않습니다. `.env`에는 `DIFY_API_BASE_URL`·`DIFY_API_KEY`·`DIFY_WORKFLOW_ID` 만 둡니다. CI 파이프라인에서만 선택적으로 `DIFY_VERIFY_*` 환경변수 폴백을 쓸 수 있습니다(스크립트 도움말 참고).

**워크플로 failed + `Request failed with status code 404` (HTTP 200인데 `data.status` 실패)**  
IDR Tier2 DSL은 **동일 `dataset_id`로** CRM `churn-risk` 와 BI `regional-heatmap` 을 둘 다 호출합니다.

| 원인 | 설명 |
|------|------|
| `period` 불일치 | BI는 CSV `period` 컬럼에 **있는 값**만 허용. 없으면 FastAPI **`No rows for period` → 404**. 진단 시 `--period 2024-01` 등으로 CSV와 맞출 것(기본값도 `2024-01`). |
| CRM 컬럼 부족 | `churn-risk` 는 `customer_code`, `order_date`, `order_amount` 필수. **SCM-only** CSV면 **404**(누락 컬럼). **`mixed_from_lis.csv`** 업로드 데이터셋이 양쪽 노드에 모두 맞습니다. |

## 가져오기 (Dify Studio)

1. Dify **Studio** → **앱 가져오기** / **DSL 가져오기** (UI 문구는 버전에 따라 다름).
2. 이 디렉터리의 `idr_crm_bi_tier2.yml` 선택.
3. 가져오기 후 **반드시** 아래를 수동 확인합니다 (DSL에 비밀값을 넣지 않음).

## 가져온 직후 필수 수정

1. **HTTP 요청 — CRM churn-risk**  
   - 인증: `Authorization: Bearer <FastAPI JWT>`  
   - JWT 발급: 프로젝트 루트에서 `.env` 에 `IDR_LOGIN_USERNAME` / `IDR_LOGIN_PASSWORD`(및 필요 시 `IDR_API_BASE_URL`) 설정 후 `make dify-fastapi-jwt-bearer` → 출력 한 줄을 Dify HTTP 노드 헤더에 붙여넣기. 스크립트: [`../scripts/fetch_fastapi_jwt.py`](../scripts/fetch_fastapi_jwt.py).  
   - URL 호스트: Podman에서 `host.containers.internal` 이 안 되면 호스트 IP 또는 `idr-net` 내 FastAPI 서비스명으로 변경.

2. **HTTP 요청 — BI regional-heatmap**  
   - 위와 동일 Bearer.

3. **LLM (Ollama)**  
   - 모델·프로바이더가 환경과 다르면 노드에서 Ollama 모델을 다시 선택.

4. **시작 변수 `period`**  
   - `regional-heatmap` 의 `period` 는 업로드된 CSV 기간 컬럼 값과 맞아야 함 (예: `2026-01`).  
   - API만 쓸 때는 `workflows/run` 의 `inputs` 에 `period` 포함.

5. **Publish** 후 API Key 발급 → 프로젝트 `.env` 의 `DIFY_API_KEY`, `DIFY_WORKFLOW_ID` 반영.  
   - 위 표 「FastAPI `.env` 와 맞출 값」과 동일: **`DIFY_WORKFLOW_ID`** 는 UUID만, **`DIFY_API_BASE_URL`** 은 uvicorn 호스트 기준 `/v1` 베이스.

## 버전 호환

DSL 은 커뮤니티 예시(`mode: workflow`, `version: 0.1.5`)와 동일 계열입니다. Dify 마이너 업그레이드 후 가져오기 오류가 나면, Studio에서 빈 Workflow 를 만든 뒤 **DSL보내기**로 형식을 한 번 비교하세요.

## AgentService 입력 키

| 키 | 용도 |
|----|------|
| `user_query` | LLM 사용자 프롬프트 |
| `dataset_id` | FastAPI 쿼리 `dataset_id` |
| `period` | BI `regional-heatmap` 필수 파라미터 |

`AgentService` 가 `period` 를 아직 넘기지 않으면, 코드 쪽에 동일 키 추가가 필요합니다.
