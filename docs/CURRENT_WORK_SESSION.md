# 현재 작업 세션 — Session 04

> **대상 Phase**: Phase 4 (서비스 계층 — data / analytics / ai)
> **전체 계획 참조**: [`docs/plans/plan.md`](docs/plans/plan.md) §Phase 4
> **워크플로 규칙**: [`docs/rules/workflow_gates.md`](docs/rules/workflow_gates.md)

---

## 진행 상태

**현재 단계**: 구현 상세 계획 작성 전

가능한 값: `구현 상세 계획 작성 전` → `구현 상세 계획 완료 — 사용자 확인 대기` (Gate A) → `구현 완료 — 사용자 확인 대기` (Gate B) → `테스트 계획 수립 완료 — 실행 승인 대기` (Gate C) → `테스트 검증 완료 — 세션 마감 대기` (Gate D 이후)

---

## 세션 워크플로 상태

| 게이트 | 완료 | 비고 |
|--------|:----:|------|
| A. 구현 상세 계획 | ⬜ | `plan`/규칙 확인 후 아래 「구현 상세 계획」작성 → **사용자 승인 후에만 코딩** |
| B. 구현 완료 | ⬜ | 구현 후 「구현 완료 요약」·체크리스트 `[x]` → 사용자 승인 후 Gate C |
| C. 테스트 상세 계획 | ⬜ | 「테스트 계획」에 상세 기록 → **사용자 승인 후에만 테스트 실행** |
| D. 테스트 검증 | ⬜ | 「테스트 검증 결과」 섹션 |
| E. 이력 이전·문서 전환 | ⬜ | `WORK_HISTORY.md` + `plan.md` 체크 후 Session 05 등으로 본 문서 교체 |

---

## 완료 기준 (Phase 4 범위)

- [`docs/plans/plan.md`](docs/plans/plan.md) **Phase 4** (4-0 CRUD → 4-1~4-3 서비스) 체크리스트 완료
- **데이터**: `ingestion_service`, `preprocessing_service` — DataFrame 불변성 (`df.copy()` 후 처리, in-place 금지) — [`backend_architecture.md`](docs/rules/backend_architecture.md) §4
- **분석**: `scm_service`, `crm_service`, `bi_service`, `routing_service`
- **AI**: `agent_service` — Dify HTTP만, **Pandas 금지**
- `ruff` / `mypy` 통과 및 세션에서 합의한 테스트 범위 통과

---

## 환경 제약 (참고)

- 앱 패키지: `idr_analytics/app/` (`PYTHONPATH=idr_analytics`)
- SDD §8, `backend_architecture.md` §2(라우팅), §4(Pandas 계층), `dify_integration.md` §4

---

## Phase 4 — 서비스 계층 (구현 체크리스트)

> **실행 순서 권장**: **4-0 CRUD** → 4-1 데이터 → 4-2 분석(SCM→CRM→BI)→`routing_service` → 4-3 `agent_service`  
> 상세 시그니처·동작은 [`docs/plans/plan.md`](docs/plans/plan.md) §Phase 4 원문을 기준으로 한다.

### 4-0. CRUD 계층 (plan.md Phase 4-0)

- [ ] `idr_analytics/app/crud/base.py` — Generic async CRUD
- [ ] `idr_analytics/app/crud/crud_user.py` — `User`
- [ ] `idr_analytics/app/crud/crud_dataset.py` — `AnalysisDataset`
- [ ] `idr_analytics/app/crud/__init__.py`

### 4-1. 데이터 계층

- [ ] `idr_analytics/app/services/data/ingestion_service.py` — `read_csv_validated()` 등 CSV → 검증된 `DataFrame`, `row_count` — DB `columns_json`·`profile_json`과 `DatasetProfileResponse` 매핑은 [`docs/plans/plan.md`](docs/plans/plan.md) §4-1 권장 JSON 구조 준수
- [ ] `idr_analytics/app/services/data/preprocessing_service.py` — `build_time_index`, `fill_missing`, `add_lag_features`, `normalize` (모두 복사 후 반환)

### 4-2. 분석 계층

- [ ] `idr_analytics/app/services/analytics/scm_service.py` — `SCMService`, Prophet 우선·ARIMA 폴백
- [ ] `idr_analytics/app/services/analytics/crm_service.py` — RFM, K-Means, `compute_churn_risk` (recency vs `CHURN_RECENCY_THRESHOLD_DAYS`)
- [ ] `idr_analytics/app/services/analytics/bi_service.py` — `regional_trend`, `yoy_comparison`, `top_tests`
- [ ] `idr_analytics/app/services/analytics/routing_service.py` — `AnalysisRoutingService`, `ComplexityScorer`와 연동, Pandas vs AI 분기

### 4-3. AI 오케스트레이션

- [ ] `idr_analytics/app/services/ai/agent_service.py` — `httpx.AsyncClient`로 Dify workflow `blocking`, 타임아웃 등 (SDD §8.4 방식 A)

### 공통

- [ ] 각 서비스 디렉터리 `__init__.py` — 필요 시 공개 심볼 re-export
- 반환 타입은 가능하면 `app/schemas/` DTO 또는 명시적 내부 결과 타입과 정렬 (Phase 5 라우터에서 재사용)

---

## 구현 상세 계획 (Gate A — 코딩 전에 AI·기여자가 작성)

_`plan.md`·SDD·`docs/rules/` 확인 후, 이번 세션에서 할 일을 순서·파일·주의사항 단위로 적는다. 작성 후 진행 상태를 「구현 상세 계획 완료 — 사용자 확인 대기」로 바꾸고, **사용자 승인 후에만** 구현을 시작한다._

—

---

## 구현 완료 요약 (Gate B — 구현 종료 시 작성)

_구현이 끝나면 여기에 변경 파일, 결정 사항, 제한 사항을 적는다. 작성 후 진행 상태를 「구현 완료 — 사용자 확인 대기」로 바꾼다._

—

---

## 테스트 계획 (Gate C — 구현 승인 후 상세 작성)

_범위(단위/통합), 우선순위, 실행 명령_

—

---

## 테스트 검증 결과 (Gate D)

_실행 일시, 통과/실패, 실패 시 조치 요약_

—

---

## 세션 마감 시 (Gate E 이후)

1. 위 게이트 표 전부 완료 확인
2. 요약 → `docs/history/WORK_HISTORY.md`
3. **`docs/plans/plan.md`** 에서 본 Phase 완료 항목 `- [x]` 반영 및 상단 「진행 현황」표 갱신
4. 본 파일을 **Session 05 — Phase 5 (API 라우터)** 중심으로 교체

---

## 다음 세션 예고 — Phase 5

`app/api/v1/endpoints/*.py` — `auth`, `datasets`, `scm`, `crm`, `bi`, `agent` (SDD §7). **엔드포인트 파일에서 `from __future__ import annotations` 금지** (`backend_architecture.md` §1).
