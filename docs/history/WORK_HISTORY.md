# 작업 이력 — IDR 시스템 데이터 분석 AI 백엔드

> **목적**: 완료된 태스크의 상세 내역을 누적 기록한다.
> `docs/CURRENT_WORK_SESSION.md`에서 완료(`- [x]`) 처리된 태스크를 이 문서로 이전한다.

---

## 기록 형식

```
## [YYYY-MM-DD] <태스크명> (plan.md Phase N)

**완료 내용**: 무엇을 구현/변경했는가
**변경 파일**: 생성/수정된 파일 목록
**결정 사항**: 구현 과정에서 내린 설계/구현 결정 및 그 이유
**특이사항**: 예상과 달랐던 점, 다음 태스크에 영향을 주는 사항
```

---

## 이력

### [2026-03-25] 프로젝트 초기 문서 체계 구축

**완료 내용**: 전체 개발 계획서 및 작업 관리 문서 체계 수립
**변경 파일**:
- `docs/plans/plan.md` — 전체 WBS (Phase 0~7, 44개 태스크)
- `.vscode/settings.json` — 한국어 Conventional Commits 커밋 메시지 설정
- `.cursorrules` — 작업 문서 체계(plan.md / CURRENT_WORK_SESSION.md / WORK_HISTORY.md / error_analysis.md) 규칙 추가
- `docs/rules/error_analysis.md` — AI 오류 분석 기록 문서 초기화
- `docs/history/WORK_HISTORY.md` — 본 파일 초기화

**결정 사항**: 작업 관리 문서를 3단계로 분리
1. `docs/plans/plan.md` — 전체 로드맵 (변경 거의 없음)
2. `docs/CURRENT_WORK_SESSION.md` — 현재 진행 중인 단위 태스크 상세 계획 (항상 최신 상태 유지)
3. `docs/history/WORK_HISTORY.md` — 완료된 태스크 아카이브 (본 파일)

**특이사항**: `CURRENT_WORK_SESSION.md`는 아직 생성되지 않음. 첫 번째 실제 개발 태스크(Phase 0 pre-flight) 시작 시 작성할 것.

### [2026-03-26] Session 01 — Phase 0 + Phase 1 Scaffolding (plan.md Phase 0~1)

**완료 내용**: Poetry 프로젝트·품질 게이트·환경 파일·`idr_analytics/` 스켈레톤·로컬/운영 Compose 분리·최소 FastAPI `/health`·로컬 Podman에서 PG/Redis 기동 검증.

**변경 파일** (주요):
- `pyproject.toml`, `poetry.lock` — 패키지 `app` (`idr_analytics/app`), Ruff/Mypy/Pytest 설정
- `.pre-commit-config.yaml`, `.gitignore`
- `.env.example`, `env.prod.example`, `.env.dev` (로컬 생성, Git 제외)
- `docker-compose.dev.yml`, `docker-compose.prod.yml`, `Dockerfile`
- `idr_analytics/app/main.py` 및 SDD §6 디렉토리·`__init__.py`

**결정 사항**:
1. 로컬은 `docker-compose.dev.yml` + **호스트** `PYTHONPATH=idr_analytics poetry run uvicorn app.main:app`; 운영은 `docker-compose.prod.yml` + `Dockerfile` (Python 3.12-slim, Phase 5에서 FastAPI 서비스 주석 해제 예정).
2. 로컬 PostgreSQL 호스트 포트 **15432** (기존 5432 점유 회피); `.env.example` / `.env.dev` 의 `DATABASE_URL` 반영.
3. RHEL rootless Podman에서 공식 Postgres/Redis 이미지가 `libc` RELRO 오류로 실패 → `postgres:15-bookworm` / `redis:7-bookworm` + `security_opt: seccomp=unconfined`, `label=disable` 적용 후 healthy 확인. (Ubuntu ga-server Docker는 동일 제약이 없을 수 있음.)

**특이사항**: 호스트에 Poetry 미설치 → `install.python-poetry.org` 로 설치. pre-commit mypy는 디렉터리 인자 중복 시 `Duplicate module` 발생 → `files:` 패턴으로 파일 단위 검사. Step 1-10(ga-server nginx / certbot)은 서버 작업으로 본 세션에서 미실행 — 배포 시 `docs/CURRENT_WORK_SESSION.md` Session 01 보관본 또는 본 이력 참고.

**프로세스 보완 (2026-03-26)**: 당시 구현 직후 사용자 확인·테스트 계획·검증 게이트 없이 `CURRENT_WORK_SESSION.md`를 Session 02로 교체한 절차는 이후 **`docs/rules/workflow_gates.md`** 및 `.cursorrules` / `project_context.md` §3단계로 보완됨. 상세는 `docs/rules/error_analysis.md` 동일 날짜 기록 참고.

### [2026-03-26] Session 02 — Phase 2 코어/DB 계층 (plan.md Phase 2)

**완료 내용**: Pydantic BaseSettings, 비동기 DB 세션, ORM 3종, Alembic 마이그레이션 2개, JWT 의존성 주입, ComplexityScorer 구현. 단위 테스트 24개 작성·검증 완료.

**변경 파일**:
- `idr_analytics/app/core/config.py` — `BaseSettings` (15개 필드), `ALLOWED_ORIGINS` JSON 파싱, `settings` 싱글턴
- `idr_analytics/app/db/base.py` — `DeclarativeBase`
- `idr_analytics/app/db/session.py` — `create_async_engine`, `async_sessionmaker`, `get_db() -> AsyncGenerator[AsyncSession, None]`
- `idr_analytics/app/models/user.py` — `User` (username unique, hashed_password, role, is_active)
- `idr_analytics/app/models/dataset.py` — `AnalysisDataset` (JSONB `columns_json`, optional `profile_json`)
- `idr_analytics/app/models/analysis_result.py` — `AnalysisResult`, `InsightBlock` (SDD §9.2)
- `idr_analytics/app/models/__init__.py` — 모델 re-export
- `idr_analytics/app/core/dependencies.py` — `OAuth2PasswordBearer`, JWT `get_current_user`, `require_admin`, `true()` WHERE
- `idr_analytics/app/core/routing.py` — `QueryType`, `Route`, `RoutingRequest`, `ComplexityScorer`
- `idr_analytics/app/py.typed` — mypy 패키지 타입 마커
- `idr_analytics/alembic/alembic.ini` — `script_location`, `prepend_sys_path=..`
- `idr_analytics/alembic/env.py` — async Alembic, `settings.DATABASE_URL` 주입
- `idr_analytics/alembic/versions/0001_initial_schema.py` — `users`, `analysis_datasets`
- `idr_analytics/alembic/versions/0002_analysis_results.py` — `analysis_results`, `insight_blocks`
- `idr_analytics/app/main.py` — 불필요한 `# type: ignore` 제거
- `pyproject.toml` — `mypy_path`, `jose.*` override, `dependencies.py` Ruff `B008` 예외
- `idr_analytics/tests/conftest.py` — env var 선주입
- `idr_analytics/tests/unit/test_routing.py` — `ComplexityScorer` 9개 케이스
- `idr_analytics/tests/unit/test_config.py` — `Settings` 파싱·기본값 8개
- `idr_analytics/tests/unit/test_dependencies.py` — `get_current_user`/`require_admin` Mock 7개

**결정 사항**:
1. `AnalysisResult.complexity_score` — 세션 초안의 `float` 대신 SDD §9.2 기준 `int | None`으로 구현.
2. `alembic.ini`를 `idr_analytics/alembic/` 안에 배치; `script_location = %(here)s`, `prepend_sys_path = ..` 설정.
3. 테스트 helper에서 async generator 대신 팩토리 함수(`_make_mock_db`)로 `AsyncSession` Mock 생성 (RuntimeWarning 제거).

**테스트 결과**: `pytest idr_analytics/tests/unit/ -v` → 24 passed, 0 failed, 0 warnings. `ruff` + `mypy` (32개 파일) 통과.

**특이사항**:
- `main.py`의 DB lifespan / 라우터 연결은 Phase 5 범위 — 미구현.
- JWT 토큰 발급(`/auth/login`)은 Phase 5 `auth` 엔드포인트에서 구현 예정.
- AI 오판 2건 `docs/rules/error_analysis.md`에 기록: (1) 구현 직후 세션 문서 전환 (Session 01 당시), (2) "작업 계획 작성" 요청 시 CreatePlan 도구 오용 (Session 02 당시).

### [2026-03-26] Session 03 — Phase 3 Pydantic 스키마(DTO) 계층 (plan.md Phase 3)

**완료 내용**: SDD §7·`dify_integration.md §2`에 맞춰 도메인별 Request/Response 및 compact DTO를 Pydantic v2로 정의. `DatasetProfileResponse`는 ORM `id`/`name` 별칭 매핑 및 프로필 필드 기본값 처리. 스키마 단위 테스트 20건 추가·전체 단위 44건 통과.

**변경 파일**:
- `idr_analytics/app/schemas/dataset.py` — `DatasetUploadRequest`, `DatasetProfileResponse`
- `idr_analytics/app/schemas/scm.py`, `crm.py`, `bi.py`, `agent.py` — SCM/CRM/BI/agent DTO 및 compact 모델
- `idr_analytics/app/schemas/__init__.py` — 공개 타입 `__all__` 재export
- `idr_analytics/tests/unit/test_schemas.py` — 스키마 단위 테스트 20개

**결정 사항**:
1. `DatasetProfileResponse`: `Field(validation_alias="id"|"name")`, `populate_by_name=True`; `columns`/`dtypes`/`null_counts`는 ORM에 없어 누락 시 빈 컬렉션 기본값 — 이후 서비스에서 프로필로 채움.
2. 엔드포인트와 달리 스키마 모듈은 `from __future__ import annotations` 허용 (`.cursorrules`).

**테스트 결과**: `pytest idr_analytics/tests/unit/test_schemas.py` 20 passed; `pytest idr_analytics/tests/unit/` 44 passed. `ruff` / `mypy` (`app/schemas/`, `test_schemas.py`) 통과.

**특이사항**: 다음 세션은 Phase 4 서비스 계층 (`docs/plans/plan.md` §Phase 4). Gate E로 본 이력 반영 및 `CURRENT_WORK_SESSION.md` → Session 04 전환.
