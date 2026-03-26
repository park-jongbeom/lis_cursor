# 현재 작업 세션 — Session 02

> **대상 Phase**: Phase 2 (코어 / DB 계층)
> **전체 계획 참조**: `docs/plans/plan.md`
> **워크플로 규칙**: `docs/rules/workflow_gates.md` (구현 → 사용자 확인 → 테스트 계획 → 검증 → 이력 이전)

---

## 진행 상태

**현재 단계**: 시작 전 (구현 전)

가능한 값: `구현 전` → `구현 완료 — 사용자 확인 대기` → `테스트 계획 수립 완료 — 실행 승인 대기` → `테스트 검증 완료 — 세션 마감 대기`

---

## 세션 워크플로 상태

| 게이트 | 완료 | 비고 |
|--------|:----:|------|
| A. 구현 | ⬜ | 체크리스트 구현 후 「구현 완료 요약」 작성 |
| B. 사용자 확인(구현) | ⬜ | 사용자 승인 후에만 테스트 계획 작성 |
| C. 테스트 계획 | ⬜ | 아래 「테스트 계획」 섹션 |
| D. 테스트 검증 | ⬜ | 아래 「테스트 검증 결과」 섹션 |
| E. 이력 이전·문서 전환 | ⬜ | `WORK_HISTORY.md` 반영 후 본 문서를 Session 03 등으로 갱신 |

---

## 완료 기준 (Phase 2 범위)

`config` + async DB 세션 + ORM 3종 + Alembic 마이그레이션 2개 + `dependencies` / `routing` + 로컬 `alembic upgrade head` 성공

---

## 환경 제약 (참고)

- 앱 패키지 경로: `idr_analytics/app/` (`PYTHONPATH=idr_analytics` 로 `import app`)
- 로컬 DB: `docker-compose.dev.yml` — PostgreSQL 호스트 포트 **15432** (`.env.dev` 의 `DATABASE_URL` 과 일치)
- 규칙: `docs/rules/backend_architecture.md`, SDD §9

---

## Phase 2 — 코어 / DB 계층 (구현 체크리스트)

> **실행 순서 권장**: 2-1 → 2-2 → 2-3 → 2-4 → 2-5

### 2-1. Config & Settings

- [ ] `idr_analytics/app/core/config.py` — Pydantic `BaseSettings`
  - Phase 1 환경 변수 전부 필드화 (`.env.dev` / `.env.example` 기준)
  - `model_config = SettingsConfigDict(env_file=".env")` (로컬은 `.env.dev` 를 `.env` 로 복사하거나 `env_file` 다중 지정)

### 2-2. DB 세션

- [ ] `idr_analytics/app/db/base.py` — `DeclarativeBase`
- [ ] `idr_analytics/app/db/session.py` — `create_async_engine`, `async_sessionmaker`, `get_db()`
  - 반환 타입: `AsyncGenerator[AsyncSession, None]` (backend_architecture.md §1)

### 2-3. ORM 모델

- [ ] `idr_analytics/app/models/user.py` — `User`
- [ ] `idr_analytics/app/models/dataset.py` — `AnalysisDataset` (SDD §9.1)
- [ ] `idr_analytics/app/models/analysis_result.py` — `AnalysisResult`, `InsightBlock` (SDD §9.2)
- [ ] `idr_analytics/app/models/__init__.py` 에 모델 export 정리

### 2-4. Alembic

- [ ] `idr_analytics/alembic/` 초기화 및 `env.py` **비동기** 마이그레이션 패턴
- [ ] `0001_initial_schema.py` — `users`, `analysis_datasets`
- [ ] `0002_analysis_results.py` — `analysis_results`, `insight_blocks`
  - downgrade 시 f-string raw SQL 금지 → `sa.table()` 등 (backend_architecture.md §5)
- [ ] 로컬에서 `alembic upgrade head` 확인

### 2-5. DI & 라우팅 코어

- [ ] `idr_analytics/app/core/dependencies.py` — `get_current_user`, `require_admin`
  - JWT + SQLAlchemy 조회 시 `where(..., true())` 등 (**bool** 리터럴 WHERE 금지)
- [ ] `idr_analytics/app/core/routing.py` — `ComplexityScorer`
  - `QueryType` 점수, 데이터 크기 페널티, `CROSS_TABLE_BONUS`, 임계값 `settings.AI_ESCALATION_THRESHOLD`

---

## 구현 완료 요약 (Gate A — 구현 종료 시 AI가 작성)

_구현이 끝나면 여기에 변경 파일, 결정 사항, 제한 사항을 적는다. 작성 후 진행 상태를 「구현 완료 — 사용자 확인 대기」로 바꾼다._

—

---

## 테스트 계획 (Gate C — 사용자가 구현을 확인한 뒤 작성)

_범위(단위/통합), 우선순위, 실행 명령 예: `PYTHONPATH=idr_analytics poetry run pytest idr_analytics/tests/ -q`_

—

---

## 테스트 검증 결과 (Gate D)

_실행 일시, 통과/실패, 실패 시 조치 요약_

—

---

## 세션 마감 시 (Gate E 이후)

1. 위 게이트 표 전부 완료 확인
2. 요약 → `docs/history/WORK_HISTORY.md`
3. 본 파일을 **Session 03 — Phase 3 (스키마)** 중심으로 교체 (다음 과제만 남김)

---

## 다음 세션 예고 — Phase 3

`idr_analytics/app/schemas/` — `dataset`, `scm`, `crm`, `bi`, `agent` DTO (SDD §7). 스키마 모듈은 `from __future__ import annotations` 사용 가능.
