# 현재 작업 세션 — Session 05

> **대상 Phase**: Phase 5 (API 라우터 계층)
> **전체 계획 참조**: [`docs/plans/plan.md`](docs/plans/plan.md) §Phase 5
> **워크플로 규칙**: [`docs/rules/workflow_gates.md`](docs/rules/workflow_gates.md)

---

## 진행 상태

**현재 단계**: 구현 상세 계획 작성 전

가능한 값: `구현 상세 계획 작성 전` → `구현 상세 계획 완료 — 사용자 확인 대기` (Gate A) → `구현 완료 — 사용자 확인 대기` (Gate B) → `테스트 계획 수립 완료 — 실행 승인 대기` (Gate C) → `테스트 검증 완료 — 세션 마감 대기` (Gate D 이후)

---

## 세션 워크플로 상태

| 게이트 | 완료 | 비고 |
|--------|:----:|------|
| A. 구현 상세 계획 | ⬜ | `plan.md`·규칙·SDD 확인 후 본 문서 「구현 상세 계획」작성 → **승인 전 코드 작성 금지** |
| B. 구현 완료 | ⬜ | 구현 후 「구현 완료 요약」·체크리스트 `[x]` → 사용자 승인 후 Gate C |
| C. 테스트 상세 계획 | ⬜ | 「테스트 계획」에 상세 기록 → **사용자 승인 후에만 테스트 실행** |
| D. 테스트 검증 | ⬜ | 「테스트 검증 결과」 섹션 |
| E. 이력 이전·문서 전환 | ⬜ | `WORK_HISTORY.md` + `plan.md` 체크 후 Session 06 등으로 본 문서 교체 |

---

## 완료 기준 (Phase 5 범위)

- [`docs/plans/plan.md`](docs/plans/plan.md) **Phase 5** 체크리스트 완료
- `app/main.py` lifespan + CORS + 라우터 마운트
- `app/api/v1/api.py` + `endpoints/` 6개 파일 (`auth`, `datasets`, `scm`, `crm`, `bi`, `agent`)
- `app/workers/arq_worker.py` — `forecast_job`, `cluster_job`
- **엔드포인트 파일에서 `from __future__ import annotations` 절대 금지** ([`backend_architecture.md §1`](docs/rules/backend_architecture.md))
- **모든 분석 엔드포인트에 `compact: bool = False` 파라미터 필수** ([`dify_integration.md §2`](docs/rules/dify_integration.md))
- `ruff` / `mypy --strict` 통과
- Gate C 승인 후 테스트 통과

---

## 환경 제약 (참고)

- 앱 패키지: `idr_analytics/app/` (`PYTHONPATH=idr_analytics`)
- 엔드포인트 파일: `from __future__ import annotations` **금지** — FastAPI Depends 런타임 resolve 실패 → 422 에러
- 서비스 주입: **모듈 레벨 싱글턴 + `Depends(lambda: svc)`** 패턴 ([`backend_architecture.md §3`](docs/rules/backend_architecture.md))
- ARQ 잡 결과: Redis 저장 + 폴링 엔드포인트. `app/workers/arq_worker.py`와 직렬화 규칙 통일

---

## Phase 5 — API 라우터 계층 (구현 체크리스트)

> 상세 시그니처·동작은 [`docs/plans/plan.md`](docs/plans/plan.md) §Phase 5 원문을 기준으로 한다.

### 5-0. FastAPI 앱 진입점

- [ ] `app/main.py` — `FastAPI(lifespan=...)` + CORS + `api_router` 마운트
- [ ] `app/api/v1/api.py` — `include_router` × 6

### 5-1. Auth

- [ ] `app/api/v1/endpoints/auth.py`
  - `POST /auth/login` → JWT 발급 (`user_crud` 조회 + passlib 검증)
  - `POST /auth/refresh` → 토큰 갱신

### 5-2. Datasets

- [ ] `app/api/v1/endpoints/datasets.py`
  - `POST /datasets/upload` — `UploadFile` + `ingestion_service` → DB 저장 (`dataset_crud.create`)
  - `GET /datasets` — 목록 조회
  - `GET /datasets/{id}/preview` — 상위 20행 (`read_csv_validated` → JSON)
  - `GET /datasets/{id}/profile` — 컬럼·프로파일 (`DatasetProfileResponse`)
  - `DELETE /datasets/{id}`

### 5-3. SCM

- [ ] `app/api/v1/endpoints/scm.py`
  - `POST /scm/forecast` — ARQ `forecast_job` 등록 → `job_id` 반환
  - `GET /scm/forecast/{job_id}` — 폴링
  - `GET /scm/restock-alert?dataset_id=&compact=false`
  - `GET /scm/seasonal-pattern?dataset_id=&compact=false`

### 5-4. CRM

- [ ] `app/api/v1/endpoints/crm.py`
  - `POST /crm/cluster` → ARQ `cluster_job`
  - `GET /crm/cluster/{job_id}`
  - `GET /crm/churn-risk?dataset_id=&top_n=20&compact=false`
  - `GET /crm/rfm-summary?dataset_id=&compact=false`

### 5-5. BI

- [ ] `app/api/v1/endpoints/bi.py`
  - `POST /bi/trend` → ARQ job
  - `GET /bi/trend/{job_id}`
  - `GET /bi/regional-heatmap?period=&test_category=&compact=false`
  - `GET /bi/yoy-comparison?dataset_id=&compact=false`
  - `GET /bi/top-tests?period=&top_n=10&compact=false`

### 5-6. Agent

- [ ] `app/api/v1/endpoints/agent.py`
  - `POST /agent/query` — `AgentQueryRequest` → `ComplexityScorer` → Pandas or Dify
  - `GET /agent/query/{session_id}`

### 5-7. ARQ 워커

- [ ] `app/workers/arq_worker.py` — `WorkerSettings` + `forecast_job`, `cluster_job`

---

## 구현 상세 계획 (Gate A — 코딩 전에 AI·기여자가 작성)

> 세션 시작 시 [`docs/plans/plan.md`](docs/plans/plan.md) §Phase 5, [`docs/rules/backend_architecture.md`](docs/rules/backend_architecture.md), [`docs/rules/dify_integration.md`](docs/rules/dify_integration.md) §2를 먼저 읽고 이 섹션을 채운다. **사용자 승인 전 코드 작성 금지.**

— 진행 시 작성 —

---

## 구현 완료 요약 (Gate B — 구현 종료 시 작성)

— 진행 시 작성 —

---

## 테스트 계획 (Gate C — 구현 승인 후 상세 작성)

— 진행 시 작성 —

---

## 테스트 검증 결과 (Gate D)

— 진행 시 작성 —

---

## 세션 마감 시 (Gate E 이후)

1. 위 게이트 표 전부 완료 확인
2. 요약 → `docs/history/WORK_HISTORY.md`
3. **`docs/plans/plan.md`** 에서 본 Phase 완료 항목 `- [x]` 반영 및 상단 「진행 현황」표 갱신
4. 본 파일을 **Session 06 — Phase 6 (Dify 인프라·연동)** 중심으로 교체

---

## 다음 세션 예고 — Phase 6

`docker-compose.dify.yml` 작성, Dify self-hosted 기동, Workflow 구성, FastAPI → Dify 연동 검증 (SDD §4.3, §10.2, `dify_integration.md §3·§5`).
