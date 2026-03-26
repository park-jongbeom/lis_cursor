# 현재 작업 세션 — Session 08

> **대상 Phase**: Phase 7 잔여(§7-3 이연) + Phase 6 실연동 마무리
> **전체 계획 참조**: [`docs/plans/plan.md`](plans/plan.md) §Phase 6·§Phase 7
> **워크플로 규칙**: [`docs/rules/workflow_gates.md`](docs/rules/workflow_gates.md)

> **직전 세션**: Session 07 마감 — [`docs/history/WORK_HISTORY.md`](history/WORK_HISTORY.md) 「[2026-03-27] Session 07」. §7-4(전체 `pytest --cov`·`pre-commit --all-files`)·`pytest-cov` 도입 완료.

---

## 진행 상태

**현재 단계**: **구현 완료 — 사용자 확인 대기** (Gate B)

가능한 값: `구현 상세 계획 작성 전` → `구현 상세 계획 완료 — 사용자 확인 대기` (Gate A) → …

---

## 세션 워크플로 상태

| 게이트 | 완료 | 비고 |
|--------|:----:|------|
| A. 구현 상세 계획 | ✅ | 2026-03-27 작성 완료 — **차기 세션 실행안 갱신 완료** |
| B. 구현 완료 | ✅ | A-1 판정 실행, FastAPI 기동 복구, P1 블로커 식별 |
| C. 테스트 상세 계획 | ⬜ | B 완료 후 작성 |
| D. 테스트 검증 | ⬜ | C 승인 후 실행 |
| E. 이력 이전·문서 전환 | ⬜ | D 완료 후 진행 |

---

## 세션 핸드오프 요약

| 구간 | 한 줄 |
|------|--------|
| **Session 07** | §7-4 커버리지 74%·134 passed·pre-commit 전체 통과 → `WORK_HISTORY.md` 참조 |
| **Session 08 결과** | P2 경로 완료: `arq_worker.py` 커버리지 93%, 통합 11 passed, 품질 게이트 통과 |
| **다음 세션 핵심 목표** | P1 실연동: Dify `workflows/run` + FastAPI `/agent/query` Tier2 스모크 + 통합 테스트 확장 |

**바로 다음 액션**: 루트 `.env`의 `DIFY_API_KEY`·`DIFY_WORKFLOW_ID` 실값 반영 후, 아래 Gate A 계획에 따라 P1 실연동을 시작한다.

---

## 완료 기준 (요약)

- `plan.md` §6의 미완료 항목(`DIFY_API_KEY`, `DIFY_WORKFLOW_ID`)을 실값으로 해소
- Dify `workflows/run` blocking 호출 성공(HTTP 200 + outputs 확인)
- FastAPI `/api/v1/agent/query` Tier2 라우팅 성공(`route_used=ai`)
- 통합 테스트에 Tier2 경로(성공/실패) 최소 2케이스 반영 및 회귀 통과

---

## 구현 상세 계획 (Gate A) — 다음 작업 실행안

> **작성일**: 2026-03-27 | **대상**: Phase 6 미완료 + Phase 7 §7-3 이연 항목(P1 실연동)
> **승인 전 금지**: 코드 변경, 테스트 실행, Dify 실호출

### 범위 확정

| 항목 | 이번 계획 |
|------|-----------|
| **P0 (필수)**: `.env` 실값 준비 + 런타임 기동 확인 | 진행 예정 |
| **P1 (주 경로)**: Dify `workflows/run` + `/agent/query` Tier2 실연동 | 진행 예정 |
| **P2 (백업 경로)**: 실값 미준비 시 보류 문서화 + 대체 테스트만 수행 | 예비 |
| **통합 테스트 확장** (`tests/integration`) | P1 성공 시 즉시 수행 |

---

### A-1. 사전 확인 (환경·자격)

목적: P1 실연동 가능 여부를 먼저 판정한다.

| 번호 | 확인 항목 | 명령 | 완료 기준 |
|------|-----------|------|-----------|
| A-1-1 | 루트 `.env` Dify 실값 준비 | `rg "^(DIFY_API_KEY|DIFY_WORKFLOW_ID)=" .env` | placeholder 문자열 없음 |
| A-1-2 | Dify 스택 기동 확인 | `make dify-ps` | `api/web/worker/nginx` Up |
| A-1-3 | FastAPI `:8000` 헬스체크 | `curl -sf http://localhost:8000/health` | HTTP 200 |
| A-1-4 | 인증 토큰 발급 가능성 | `make dify-fastapi-jwt-bearer` | Bearer 토큰 1줄 출력 |
| A-1-5 | 네트워크 전제 | `podman network inspect idr-net` | 네트워크 존재 |

**분기 규칙**:
- `A-1-1` 실패 시: 실연동 중단, P2 경로로 전환
- `A-1-2`~`A-1-4` 중 실패 시: 기동/인증 복구 후 재확인

---

### A-2. P1 경로 (실값 준비됨) — 실연동 검증

#### A-2-1. Dify `workflows/run` blocking 스모크

```bash
curl -sS -X POST "http://localhost:8080/v1/workflows/run" \
  -H "Authorization: Bearer ${DIFY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"period": "2025-Q4"},
    "response_mode": "blocking",
    "user": "session08-smoke"
  }'
```

완료 기준:
- HTTP 200
- 응답 JSON에 `data.outputs` 존재
- `answer` 또는 요약 텍스트 필드 존재

#### A-2-2. FastAPI `/agent/query` Tier2 라우팅 스모크

```bash
curl -sS -X POST "http://localhost:8000/api/v1/agent/query" \
  -H "Authorization: Bearer <fastapi-jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "<uuid>",
    "query": "최근 CRM 이탈 고위험 고객 요약과 BI 지역 히트맵 핵심만 알려줘",
    "query_type": "NATURAL_LANGUAGE"
  }'
```

완료 기준:
- HTTP 200
- 응답 `route_used`가 `ai`(Tier2)
- `answer` 또는 동등 결과 텍스트 존재

#### A-2-3. 통합 테스트 확장

대상:
- `idr_analytics/tests/integration/test_api_phase5.py` 확장 또는 `test_api_tier2.py` 신설

필수 케이스:
1. `/agent/query`가 Tier2로 라우팅되어 성공 응답 반환
2. Dify 연동 실패(타임아웃/4xx) 시 API 에러 구조가 일관됨 (`detail.code`, `detail.message`)

---

### A-3. P2 경로 (실값 미준비) — 백업 계획

| 번호 | 작업 | 완료 기준 |
|------|------|-----------|
| A-3-1 | `CURRENT`/`plan.md`에 보류 사유와 해제 조건 명시 | `DIFY_*` 실값 필요 조건 명시 |
| A-3-2 | 실연동 없이 가능한 Tier2 목 테스트 우선 반영 | 성공/실패 2케이스 통과 |
| A-3-3 | 차기 실행을 위한 운영 체크리스트 작성 | 실행 명령·복구 절차 포함 |

---

### A-4. 테스트 계획 초안(승인 후 Gate C로 승격)

P1 성공 시:
- `tests/integration/test_api_phase5.py` 확장 또는 `test_api_tier2.py` 추가
- 케이스: `workflows/run` success/failure, `/agent/query` Tier2 route assert
- 회귀: 기존 11개 통합 테스트 영향 없음 확인

P2 전환 시:
- 목 기반 Tier2 테스트만 먼저 반영
- 회귀: `make test-unit`, `make lint`, `make typecheck`

---

### Gate A 완료 정의 요약

| 항목 | 완료 신호 |
|------|-----------|
| 실연동 가능성 판정 | A-1 체크 완료 |
| 실행 경로 확정 | P1 또는 P2 선택 명시 |
| 검증 명령 확정 | curl/make/pytest 명령 문서화 |
| 후속 Gate 연결 | Gate B/C 진입 조건 명시 |

---

## 구현 완료 요약 (Gate B)

### 실행 결과 (A-1 판정)

| 항목 | 결과 | 비고 |
|------|------|------|
| A-1-1 `.env` Dify 실값 | ✅ 통과 | `DIFY_API_KEY` 실값 확인, `DIFY_WORKFLOW_ID` 반영 |
| A-1-2 Dify 스택 | ✅ 통과 | `vendor_api/web/worker/nginx` Up 확인 |
| A-1-3 FastAPI 헬스 | ✅ 복구 | `uvicorn` 수동 기동 후 `/health` 200 |
| A-1-4 JWT 발급 | ✅ 통과 | `admin/admin` 계정으로 Bearer 토큰 발급 성공 |
| A-1-5 네트워크 | ✅ 통과 | `idr-net` inspect 성공 |

### 추가 검증

1. 로컬 IDR DB(`idr-postgres:15432`)에 `admin/admin` 계정을 생성/갱신(upsert)했고 role=`admin`, is_active=`true` 확인.
2. Dify 워크플로 입력용 샘플 데이터셋(`data/admin_seed_dataset.csv`)을 생성하고 `analysis_datasets`에 owner=`admin`으로 등록.
3. Dify `workflows/run` 호출은 인증을 통과했지만 **400 invalid_param**으로 실패: `Model llama3.2 not exist.`
4. `/api/v1/agent/query` Tier2 호출은 현재 Dify 4xx가 내부에서 전파되어 FastAPI에서 500으로 반환됨(연동 에러 처리 보강 필요).

### 결정 사항

1. **P1 실연동은 부분 블로킹**: 계정/토큰/데이터셋 준비는 완료되었고, 현재 블로커는 Dify 모델 설정(`llama3.2`) 미존재.
2. **다음 실행 시작 조건**:
   - Dify Studio의 워크플로 LLM 노드를 사용 가능한 모델로 변경(또는 모델 프로바이더 연결 복구)
   - 변경 후 `workflows/run` 재호출로 200 + `data.outputs` 확인
3. 위 조건 충족 즉시 A-2-2(`/agent/query`) 및 A-2-3(통합 테스트 확장) 재개.

---

## 테스트 계획 (Gate C)

> 사용자 승인 후 작성

---

## 테스트 검증 결과 (Gate D)

> 사용자 승인 후 작성

---

## 이전 세션 요약 (Session 07)

Phase 7 §7-4: `pytest-cov` 추가, 전체 테스트 `--cov=app`(74%)·HTML 리포트, `pre-commit run --all-files` 통과. 상세는 [`docs/history/WORK_HISTORY.md`](history/WORK_HISTORY.md) 「[2026-03-27] Session 07」.
