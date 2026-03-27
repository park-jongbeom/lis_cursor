# 현재 작업 세션 — Session 17

> **대상 Phase**: Phase 9 — 강의 데모 UI (강의 전 수동 검증)
> **전체 계획 참조**: [`docs/plans/plan.md`](plans/plan.md) §Phase 9
> **워크플로 규칙**: [`docs/rules/workflow_gates.md`](rules/workflow_gates.md)

> **직전 세션**: Session 16 마감 — [`docs/history/WORK_HISTORY.md`](history/WORK_HISTORY.md) 「[2026-03-27] Session 16 — Phase 9 강의 데모 UI: `demo/*`·`env.example`·Gate A~E」.

---

## 진행 상태

**현재 단계**: **테스트 검증 완료 — 세션 마감(Gate E) 대기**

- Gate D: 사용자 「Gate C대로 실행·기록까지」(2026-03-27) 승인 → C-2 `make test` + C-1.1 개발 스택 스모크 완료. §테스트 검증 결과 참조.

---

## 환경·전제

| 항목 | 참조 |
|------|------|
| FastAPI | 호스트 uvicorn `:8000`, `demo/README.md` 절차 |
| Dify | `make dify-up` 등, Studio `:8080`, 워크플로 `idr_crm_bi_tier2` **Publish** |
| 데모 UI | `demo/index.html` + Live Server(또는 동일 출처), `ALLOWED_ORIGINS`·`INTERNAL_BYPASS_*` |
| ARQ | SCM `forecast`·CRM `cluster` 시연 시 워커·Redis 동일 설정 필요 (`DEMO_SCRIPT.md` 주의) |
| 샘플 데이터 | **`demo/sample_data/`** (`scm_sample.csv`·`crm_sample.csv`·`bi_sample.csv`, `DEMO_SAMPLES_PLAN.md`) — `plan.md` §P9-1 부록 C와 병행 가능 |

---

## 세션 워크플로 상태

| 게이트 | 완료 | 비고 |
|--------|:----:|------|
| A. 구현 상세 계획 | ✅ | 사용자 「진행해라」승인(2026-03-27) |
| B. 구현 완료 | ✅ | P9-1 본선: 코드 변경 없음(이전). **데모 샘플**: `demo/sample_data/` 추가 — §Gate B |
| C. 테스트 상세 계획 | ✅ | §테스트 계획 — 실행 승인 후 Gate D 반영됨 |
| D. 테스트 검증 | ✅ | 2026-03-27 — §테스트 검증 결과 |
| E. 이력 이전·문서 전환 | ⬜ | 강의 후 또는 사용자 지시 시 |

---

## 세션 핸드오프 요약

| 구간 | 한 줄 |
|------|--------|
| **Session 16 결과** | `demo/index.html`·README·`DEMO_SCRIPT.md`·`env.example`; `make test` **134+15** 통과; 브라우저 E2E·P9-1은 **미실시** |
| **Session 17 (본 세션) 자동 회귀** | `make test` **134+18** (샘플 CSV 통합 3건: `test_api_sample_data_upload.py`) |
| **Session 17 초점** | **3/28 강의 전** `demo/DEMO_SCRIPT.md`·`plan.md` §P9-1·`demo/index.html` 브라우저 스모크 |

**바로 다음 액션**: **C-1 나머지**(브라우저·샘플 CSV·선택 ARQ/Dify) 사용자 리허설 → 필요 시 **Gate E**(`WORK_HISTORY`, `plan.md`, 다음 세션 `CURRENT`).

---

## 완료 기준 (초안)

- [ ] `demo/DEMO_SCRIPT.md` 리허설 체크리스트 전항 확인(가능한 범위)
- [x] FastAPI `/health` 200 — 인프라 기동·`make migrate`·일시 uvicorn으로 확인(2026-03-27, 에이전트)
- [ ] `plan.md` §P9-1 나머지(Dify Publish·Bearer·샘플 사전 업로드·LLM 1회) — 브라우저/Studio에서 사용자 확인
- [ ] `demo/index.html` 강의 동선 최소 1회 브라우저 통과
- [ ] (강의 후) Phase 9 완료 표·`WORK_HISTORY`·`plan.md` 진행 표 정리 — Gate E

---

## 구현 상세 계획 (Gate A)

### 1. 목적·범위

| 구분 | 내용 |
|------|------|
| **목적** | 2026-03-28 강의 전에 시연 경로(P9-1 + 데모 UI + Dify)가 한 번이라도 통과하는지 확인하고, `demo/DEMO_SCRIPT.md` 리허설 체크를 채운다. |
| **산출물** | Gate D에 **수동 검증 메모**(일시, 통과/스킵 사유, 이슈·우회) + 필요 시 `plan.md` §P9-1 체크 반영 증적. |
| **코드** | **변경 없음을 기본**으로 한다. 데모/백엔드 **버그·오타·긴급 CORS만** 사용자 지시 시 최소 수정. |

### 2. 작업 순서 (실행 순서 고정)

1. **문서 동기화 확인** (읽기만)  
   - `docs/plans/plan.md` §Phase 9 · §P9-1 체크리스트  
   - `demo/README.md`, `demo/DEMO_SCRIPT.md`  
   - `ref_files/컨설팅계획서_김희원_IDR시스템즈_전문가_양식.md` (시간 배분 참고)

2. **P9-1 인프라·백엔드 점검** (`plan.md` §P9-1와 동일 계열)  
   - Dify 스택 기동·`:8080` 로그인·대상 워크플로 **Publish**  
   - FastAPI `/health`(또는 `/docs`) 200  
   - HTTP Request 노드용 Bearer 갱신·Dify 쪽 반영 (`make dify-fastapi-jwt-bearer` 등, `README`/운영 문서 절차 따름)  
   - (선택) 샘플 CSV 3종 사전 업로드로 강의 중 대기 시간 축소

3. **`demo/DEMO_SCRIPT.md` 리허설 체크리스트** (해당 파일 상단 체크박스 순서 권장)  
   - curl/브라우저 헬스  
   - 데모 HTML: 업로드 → **SCM / CRM / BI 중 최소 1개** 성공 경로  
   - Tier2: 데모 「Dify AI 요약」 또는 Dify 앱에서 LLM 응답 1회  
   - 노트북 절전·방화벽·VPN

4. **강의 스크립트 동선 리허설** (`DEMO_SCRIPT.md` 본문 1~4단계)  
   - 오전: Cursor·Gate A~E·`/docs`·`compact=true` (5+5분 분량 맞는지 타이밍만 확인)  
   - 오후: `demo/index.html` 탭 동선(업로드 → dataset_id → CRM Bar 또는 BI 히트맵 → 가능하면 SCM)  
   - Dify Studio 노드 설명 → 앱 실행 스트리밍  
   - **SCM/CRM ARQ 잡**: 워커 미기동 시 `pending` 가능 — 리허설 때 워커 여부를 명시적으로 확인

5. **이슈 기록**  
   - 체크 실패·우회 사용 시 `DEMO_SCRIPT.md` §「문제 발생 시 짧은 우회」와 대조해 원인 한 줄 기록 → Gate D에 옮김.

### 3. 구현(Gate B)에 대한 해석

| 경우 | Gate B 처리 |
|------|----------------|
| 코드·설정 변경 없음 | 「구현 완료 요약」에 **코드 변경 없음**, 수동 점검만 수행했음을 명시. |
| 긴급 수정 발생 | 승인된 최소 범위만 반영 후 변경 파일·사유를 Gate B에 기록. |

### 4. 테스트(Gate C~D)에 대한 해석

| 구분 | 내용 |
|------|------|
| 자동 | 이번 세션 **필수 아님** — Session 16에서 `make test` 회귀 완료 전제. |
| 수동 | Gate C는 **체크리스트 + 기대 결과**를 `CURRENT`에 한 블록으로 적고, 승인 후 D에서 실행·메모. (`workflow_gates.md`: 수동이면 A에 흡수 가능하나, 실행 전 승인 원칙은 동일.) |

### 5. 완료·마감 (Gate E)

- 강의(또는 리허설 종료) 후: `WORK_HISTORY.md`에 Session 17 요약, `plan.md` §P9-1·Phase 9 완료 표·진행 표 동기화, `CURRENT`를 다음 세션용으로 교체.

### 6. 리스크·주의

- **Gate A 승인 없이** 코드 수정 금지.  
- **Gate A 승인만으로** `make test`/`pytest` 자동 실행 금지 — 사용자가 테스트까지 명시 승인한 경우에만 (`IDR 세션 SKILL` Gate B 직후 멈춤).  
- `.env`·토큰·실키는 Git에 올리지 않음 (`project_context.md`).

---

## 구현 완료 요약 (Gate B)

### 코드·설정

- **데모 샘플·문서 (사용자 승인 후)**  
  - 추가: `demo/sample_data/scm_sample.csv`, `crm_sample.csv`, `bi_sample.csv`  
  - 추가: `demo/sample_data/DEMO_SAMPLES_PLAN.md` (상세 계획·검증 기준), `demo/sample_data/README.md`  
  - 수정: `demo/README.md` — 샘플 디렉터리 안내 1줄  
  - `crm_sample.csv`: `DEMO_SAMPLES_PLAN.md` §3.2 정합(필수 3컬럼·고객 수·과거 마지막 주문). README 필수 컬럼 설명 정정.  
- **통합 테스트**: `idr_analytics/tests/integration/test_api_sample_data_upload.py` — 저장소 `demo/sample_data/*.csv` 멀티파트 업로드 → `GET .../profile` · SCM restock / CRM churn / BI heatmap·YoY (테스트 DB). 파일명으로 수집 순서를 `test_arq_worker_integration` 앞에 두어 async 엔진 루프 충돌 방지.
- **앱 런타임**: SCM/CRM/BI **프로덕션 코드 경로 변경 없음**(샘플·문서·pytest 추가만).

### 에이전트가 수행한 검증 (2026-03-27)

| 항목 | 결과 |
|------|------|
| 초기 `curl :8000/health` | 연결 거부(백엔드 미기동 상태) |
| `make dev-up` | `idr-postgres`·`idr-redis` 기동 성공 |
| `make migrate` | `0003_timestamptz`까지 적용 완료 |
| 일시 uvicorn + `GET /health` | **200**, `{"status":"ok"}` |
| `http://127.0.0.1:8080` | 응답 있음(이 환경에서 Dify NGINX 동작 중으로 추정 — HTML 일부 `/apps`) |

### 사용자(브라우저)에서 아직 필요한 작업

- `demo/sample_data/` CSV로 **탭별 업로드 → 분석 1경로** 스모크(계획서 §5 체크리스트, `DEMO_SAMPLES_PLAN.md`).
- `demo/DEMO_SCRIPT.md` 상단 체크리스트: Dify 로그인·**Publish**·Bearer 반영·데모 HTML 업로드→분석 1경로·Tier2 LLM 1회·네트워크 절전 등.
- 강의 스크립트 타이밍 리허설.
- SCM/CRM ARQ 시연 시 워커 기동 여부 확인 (`demo/README.md`).

### 참고

- uvicorn 프로세스는 헬스 확인 후 종료함. 강의 전에는 `demo/README.md` 3-step대로 백그라운드 기동 유지.
- **`make test`/pytest는 Gate C 승인 전 실행하지 않음** (워크플로).

---

## 테스트 계획 (Gate C)

> **범위**: 웹 브라우저 수동 시연 + (선택) 저장소 자동 테스트.  
> **실행**: 본 섹션 승인 후 Gate D에서 수행. `make test`/pytest는 **별도 명시 승인** 시에만.

### C-0. 로컬 DB 구분 (질문에 대한 답)

| 구분 | 용도 | Postgres(호스트) | DB 이름 | Redis(호스트) | 비고 |
|------|------|------------------|---------|---------------|------|
| **개발 스택** | 일상 개발·**브라우저 데모**(`uvicorn` + `demo/index.html`) | **15432** | `idr_analytics` (`.env` 기준) | **6379** | `make dev-up` + `.env`의 `DATABASE_URL` / `REDIS_URL` |
| **테스트 스택** | **pytest** (`make test` → `test-integration` 등) | **15433** | `idr_test` | **6380** | `docker-compose.test.yml` (`name: idr-test`), `migrate-test` |

- 둘 다 **본인 PC의 로컬 컨테이너 DB**이지만 **서로 다른 인스턴스**다. 브라우저로 API를 띄울 때는 기본적으로 **개발 DB(15432)** 에 데이터가 쌓인다.  
- **pytest 통합 테스트는 테스트 DB(15433)** 를 쓰며, 브라우저에서 친 업로드 데이터와 **공유되지 않는다**.

### C-1a. 샘플 CSV 전용 상세 테스트 계획 (업로드·DB·API)

**목적**: `demo/sample_data/*.csv` 로 **실제 적재·분석**이 되는지 증명한다. **자동**: `make test` 통합 모듈 `idr_analytics/tests/integration/test_api_sample_data_upload.py` 가 테스트 DB에서 3종 업로드·프로필·핵심 분석 API까지 검증한다. **수동**(브라우저·Dify·ARQ 폴링 등)은 여전히 아래·`SAMPLE_DATA_TEST_PLAN.md`가 필요하다.

| 참조 | 내용 |
|------|------|
| **단일 원본** | [`demo/sample_data/SAMPLE_DATA_TEST_PLAN.md`](../demo/sample_data/SAMPLE_DATA_TEST_PLAN.md) — 트랙 A/B, TC-SCM-/CRM-/BI-, `row_count` 기대값, curl·SQL |
| **보조** | [`demo/sample_data/DEMO_SAMPLES_PLAN.md`](../demo/sample_data/DEMO_SAMPLES_PLAN.md) §5 체크리스트 |

### C-1. 수동 — 브라우저 데모 (개발 DB 전제)

**전제**: `make dev-up`, `make migrate`, `.env`에 `DATABASE_URL`→`localhost:15432`, `REDIS_URL`→`6379`, 데모용 CORS·`admin` 시드는 `demo/README.md`.  
**샘플 파일 기준 시나리오**는 **C-1a** 문서를 우선한다.

| 단계 | 절차 | 기대 |
|------|------|------|
| C-1.1 | `curl -sf http://127.0.0.1:8000/health` (또는 `/docs`) | 200 |
| C-1.2 | `demo/index.html` — JWT 또는 우회 Bearer 설정 후 **로그인/인증** 확인 | 401 없이 이후 요청 가능 |
| C-1.3 | `demo/sample_data/scm_sample.csv` 업로드, `dataset_type=**scm**` | `dataset_id` 발급, 프로필에 컬럼 3개 |
| C-1.4 | SCM 탭 — 기본 컬럼 그대로 **예측 실행 → 폴링** | `(선택)` ARQ 워커 기동 시 `completed`, 차트·`forecasts` 존재 |
| C-1.5 | `crm_sample.csv` 업로드, `dataset_type=**crm**` | 동일 |
| C-1.6 | CRM 탭 — **이탈 위험 분석** | 200, 표/차트 |
| C-1.7 | CRM 탭 — **클러스터 실행 → 폴링** | `(선택)` 워커 기동 시 잡 완료 |
| C-1.8 | `bi_sample.csv` 업로드, `dataset_type=**bi**` | 동일 |
| C-1.9 | BI 탭 — `period=**2024-01**`(CSV와 동일 문자열) **지역 히트맵** | 200, 표·차트 |
| C-1.10 | BI 탭 — **YoY 비교** (`year`, `value` 기본값) | 200 |
| C-1.11 | (선택) Dify `:8080` — `dataset_id`·`period` 동일로 워크플로 1회 | LLM·HTTP 노드 스모크 |

**기록(Gate D)**: 일시, 성공/실패 단계, ARQ 유무, 스크린샷 저장 경로(선택).

### C-2. 자동 — pytest (테스트 DB 전제)

**전제**: README §테스트 — `unset ALLOWED_ORIGINS` 등, `make test`는 `15433`/`6380` 스택 기동 후 실행.

| 단계 | 명령 | 기대 |
|------|------|------|
| C-2.1 | `make test` (또는 `test-infra-up` → `migrate-test` → `test-unit` → `test-integration` → `test-infra-down`) | 단위·통합 전부 통과 |

브라우저 검증을 **pytest로 대체할 수 없음**(UI·ARQ·Dify는 별도).

### C-3. 금지·주의

- 브라우저 데모 중 `.env`의 `DATABASE_URL`을 **15433**으로 바꿔도 되나, 그때는 **개발용 시드·데이터가 테스트 DB에만** 생기므로 혼동 주의. 일반적으로 **데모=15432** 로 통일 권장.  
- `make test` 실행 중에는 테스트 스택이 **잠깐** dev와 함께 떠 있을 수 있으나, 포트가 달라 충돌 없음(15432 vs 15433).

---

## 테스트 검증 결과 (Gate D)

**일시**: 2026-03-27 (에이전트 실행)  
**승인**: 사용자 「Gate C대로 실행·기록까지」

### C-2 자동 테스트 (테스트 DB `localhost:15433`, Redis `6380`)

| 항목 | 결과 |
|------|------|
| 명령 | `unset ALLOWED_ORIGINS && make test` (저장소 루트) |
| 인프라 | `podman-compose -f docker-compose.test.yml up -d` → healthy → `migrate-test` → `test-infra-down` |
| 단위 | **134 passed** (~2.2s) |
| 통합 | **18 passed** (~20s) — 기존 15 + 데모 샘플 CSV 3건 (`test_api_sample_data_upload.py`, 수집 순서상 `test_arq_worker_integration` **앞**에 실행) |
| 합계 | **152 passed**, exit code **0** |

### C-1 수동·브라우저 계열 (개발 DB `localhost:15432`)

| 단계 | 실행 주체 | 결과 |
|------|------------|------|
| C-1.1 `/health`, `/docs` | 에이전트 | `make dev-up`·`make migrate` 후 `uvicorn` 일시 기동 → `GET /health` **200** `{"status":"ok"}`, `/docs` **200**. 이후 uvicorn 종료. |
| C-1.2 ~ C-1.11 | 사용자 | **미실시**(JWT/우회, `demo/index.html` 업로드·탭·선택 Dify). 브라우저에서 `demo/sample_data/DEMO_SAMPLES_PLAN.md` §5 체크리스트로 확인 권장. |

### 특이사항

- 테스트 스택 기동 시 postgres healthcheck 로그에 일시 `unhealthy` 표기 후 healthy로 전환(기존과 동일 패턴).
- 샘플 CSV 통합 테스트 구간에서 statsmodels ARIMA 관련 **UserWarning·ConvergenceWarning** 수개(회귀 실패 아님).
- C-1.2~ 브라우저·Dify·ARQ 수동 구간은 에이전트가 대신할 수 없음 — 사용자 환경에서 리허설 시 `demo/DEMO_SCRIPT.md` 유지.

---

## 이전 세션 요약 (Session 16)

데모 UI 3종 + `env.example` 보강, 전체 pytest 회귀 통과. 상세는 [`docs/history/WORK_HISTORY.md`](history/WORK_HISTORY.md) 동일 제목 항목.
