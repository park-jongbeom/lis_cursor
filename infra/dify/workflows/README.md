# Dify Workflow DSL (IDR)

## 파일

| 파일 | 설명 |
|------|------|
| [`idr_crm_bi_tier2.yml`](idr_crm_bi_tier2.yml) | CRM `churn-risk` + BI `regional-heatmap` (둘 다 `compact=true`) → 변수 집계자 → LLM → 종료 |

흐름·엔드포인트 근거: [`docs/rules/dify_integration.md`](../../../docs/rules/dify_integration.md) §3.2.

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

## 버전 호환

DSL 은 커뮤니티 예시(`mode: workflow`, `version: 0.1.5`)와 동일 계열입니다. Dify 마이너 업그레이드 후 가져오기 오류가 나면, Studio에서 빈 Workflow 를 만든 뒤 **DSL보내기**로 형식을 한 번 비교하세요.

## AgentService 입력 키

| 키 | 용도 |
|----|------|
| `user_query` | LLM 사용자 프롬프트 |
| `dataset_id` | FastAPI 쿼리 `dataset_id` |
| `period` | BI `regional-heatmap` 필수 파라미터 |

`AgentService` 가 `period` 를 아직 넘기지 않으면, 코드 쪽에 동일 키 추가가 필요합니다.
