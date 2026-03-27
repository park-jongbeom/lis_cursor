# 현재 작업 세션 — Session 17

> **대상 Phase**: Phase 9 — 강의 데모 UI (강의 전 수동 검증)
> **전체 계획 참조**: [`docs/plans/plan.md`](plans/plan.md) §Phase 9
> **워크플로 규칙**: [`docs/rules/workflow_gates.md`](rules/workflow_gates.md)

> **직전 세션**: Session 16 마감 — [`docs/history/WORK_HISTORY.md`](history/WORK_HISTORY.md) 「[2026-03-27] Session 16 — Phase 9 강의 데모 UI: `demo/*`·`env.example`·Gate A~E」.

---

## 진행 상태

**현재 단계**: **구현 완료 — 사용자 확인 대기** (Gate B)

코드 변경 없음. CLI·일시 uvicorn으로 **개발 DB/Redis 기동·마이그레이션·`/health` 200**만 확인함. 브라우저·Dify Studio·Bearer·LLM 리허설은 **사용자 수동** (`docs/rules/workflow_gates.md`).

---

## 환경·전제

| 항목 | 참조 |
|------|------|
| FastAPI | 호스트 uvicorn `:8000`, `demo/README.md` 절차 |
| Dify | `make dify-up` 등, Studio `:8080`, 워크플로 `idr_crm_bi_tier2` **Publish** |
| 데모 UI | `demo/index.html` + Live Server(또는 동일 출처), `ALLOWED_ORIGINS`·`INTERNAL_BYPASS_*` |
| ARQ | SCM `forecast`·CRM `cluster` 시연 시 워커·Redis 동일 설정 필요 (`DEMO_SCRIPT.md` 주의) |
| 샘플 데이터 | `plan.md` §P9-1 부록 C 3종 — 사전 업로드 권장 |

---

## 세션 워크플로 상태

| 게이트 | 완료 | 비고 |
|--------|:----:|------|
| A. 구현 상세 계획 | ✅ | 사용자 「진행해라」승인(2026-03-27) |
| B. 구현 완료 | ✅ | 코드 변경 없음 — §Gate B 요약 참조 |
| C. 테스트 상세 계획 | ⬜ | 수동만이면 Gate A에 흡수 가능 |
| D. 테스트 검증 | ⬜ | 리허설 체크 기록 |
| E. 이력 이전·문서 전환 | ⬜ | 강의 후 Phase 9 완료 표 시 |

---

## 세션 핸드오프 요약

| 구간 | 한 줄 |
|------|--------|
| **Session 16 결과** | `demo/index.html`·README·`DEMO_SCRIPT.md`·`env.example`; `make test` **134+15** 통과; 브라우저 E2E·P9-1은 **미실시** |
| **Session 17 초점** | **3/28 강의 전** `demo/DEMO_SCRIPT.md`·`plan.md` §P9-1·`demo/index.html` 브라우저 스모크 |

**바로 다음 액션**: 사용자 Gate B 확인 후 → Gate C(수동 리허설 체크리스트) 승인 → Gate D 기록. **`make test`는 Gate C 승인 전 금지.**

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

- **변경 파일 없음** (저장소 diff 없음).

### 에이전트가 수행한 검증 (2026-03-27)

| 항목 | 결과 |
|------|------|
| 초기 `curl :8000/health` | 연결 거부(백엔드 미기동 상태) |
| `make dev-up` | `idr-postgres`·`idr-redis` 기동 성공 |
| `make migrate` | `0003_timestamptz`까지 적용 완료 |
| 일시 uvicorn + `GET /health` | **200**, `{"status":"ok"}` |
| `http://127.0.0.1:8080` | 응답 있음(이 환경에서 Dify NGINX 동작 중으로 추정 — HTML 일부 `/apps`) |

### 사용자(브라우저)에서 아직 필요한 작업

- `demo/DEMO_SCRIPT.md` 상단 체크리스트: Dify 로그인·**Publish**·Bearer 반영·데모 HTML 업로드→분석 1경로·Tier2 LLM 1회·네트워크 절전 등.
- 강의 스크립트 타이밍 리허설.
- SCM/CRM ARQ 시연 시 워커 기동 여부 확인 (`demo/README.md`).

### 참고

- uvicorn 프로세스는 헬스 확인 후 종료함. 강의 전에는 `demo/README.md` 3-step대로 백그라운드 기동 유지.
- **`make test`/pytest는 Gate C 승인 전 실행하지 않음** (워크플로).

---

## 테스트 계획 (Gate C)

> 해당 시 작성 (수동만이면 체크리스트 + 스크린샷/메모 경로)

---

## 테스트 검증 결과 (Gate D)

> 해당 시 작성

---

## 이전 세션 요약 (Session 16)

데모 UI 3종 + `env.example` 보강, 전체 pytest 회귀 통과. 상세는 [`docs/history/WORK_HISTORY.md`](history/WORK_HISTORY.md) 동일 제목 항목.
