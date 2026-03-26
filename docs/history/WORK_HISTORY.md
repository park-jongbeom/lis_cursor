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

### [2026-03-26] Session 04 — Phase 4 서비스 계층 + 테스트 전용 DB 환경 구축 (plan.md Phase 4)

**완료 내용**: CRUD 기반(Generic) + 도메인별 CRUD, 데이터·분석·AI 서비스 계층 전체 구현. Phase 4 단위 테스트 10파일 123케이스 작성·검증. 테스트 전용 docker 격리 환경(PG 15433, Redis 6380) 구축 및 마이그레이션 완료.

**변경·신규 파일**:

*CRUD 계층*
- `idr_analytics/app/crud/base.py` — `CRUDBase[ModelT]`: `get`, `get_multi`, `create`, `update`, `delete` (commit+refresh 정책 통일, `delete` 미존재 시 `ValueError`)
- `idr_analytics/app/crud/crud_user.py` — `CRUDUser` + `get_by_username`, `user_crud` 싱글턴
- `idr_analytics/app/crud/crud_dataset.py` — `CRUDDataset` + `get_multi_by_owner`, `dataset_crud` 싱글턴
- `idr_analytics/app/crud/__init__.py` — `user_crud`, `dataset_crud` re-export

*데이터 계층*
- `idr_analytics/app/services/data/ingestion_service.py` — `read_csv_validated`, `build_columns_profile`, `IngestionService`, `ingestion_service`
- `idr_analytics/app/services/data/preprocessing_service.py` — `build_time_index`, `fill_missing`, `add_lag_features`, `normalize` (전부 `df.copy()` 후 반환), `preprocessing_service`
- `idr_analytics/app/services/data/__init__.py`

*분석 계층*
- `idr_analytics/app/services/analytics/scm_service.py` — `SCMService.forecast`: 그룹별 Prophet(행 60 이상) → ARIMA(1,1,1) 폴백, `ThreadPoolExecutor`, `_trend_from_yhat`, `scm_service`
- `idr_analytics/app/services/analytics/crm_service.py` — `build_rfm_features`(백분위 점수), `cluster`(K-Means), `CRMService.compute_churn_risk`, `crm_service`. CSV 컬럼 가정: `customer_code`, `order_date`, `order_amount`(필수), `customer_name`(선택)
- `idr_analytics/app/services/analytics/bi_service.py` — `regional_trend`, `yoy_comparison`, `top_tests`, `bi_service`
- `idr_analytics/app/services/analytics/routing_service.py` — `AnalysisRoutingService.route`(컨텍스트 dataclass + `ComplexityScorer` 분기), `routing_service`
- `idr_analytics/app/services/analytics/__init__.py`

*AI 계층*
- `idr_analytics/app/services/ai/agent_service.py` — `AgentService.analyze`: `POST .../workflows/run`, `workflow_id`·`inputs`·`blocking`·timeout 120s, 응답 `data.outputs.answer` 매핑, `agent_service`
- `idr_analytics/app/services/ai/__init__.py`
- `idr_analytics/app/services/__init__.py`

*테스트*
- `idr_analytics/tests/unit/test_crud_base.py`, `test_crud_user.py`, `test_crud_dataset.py`
- `idr_analytics/tests/unit/test_ingestion_service.py`, `test_preprocessing_service.py`
- `idr_analytics/tests/unit/test_scm_service.py`, `test_crm_service.py`, `test_bi_service.py`
- `idr_analytics/tests/unit/test_routing_service.py`, `test_agent_service.py`
- `idr_analytics/tests/conftest.py` — DB URL `localhost:15433/idr_test`로 수정

*테스트 인프라*
- `docker-compose.test.yml` — PG 포트 15433, Redis 6380, `idr-test-net` 격리
- `.env.test` — 테스트 전용 환경 변수 (`.gitignore` 등록)
- `Makefile` — `test-infra-up/down`, `migrate-test`, `test-unit`, `test-unit-cov`, `check` 타겟
- `.gitignore` — `.env.test` 추가

*품질 게이트*
- `pyproject.toml` — dev `pandas-stubs`, mypy override (`prophet`, `sklearn.*`, `statsmodels.tsa.arima.model`)
- `poetry.lock` — 재생성

**결정 사항**:
1. **CRM CSV 컬럼(가정)**: `customer_code`, `order_date`, `order_amount` 필수. `customer_name`은 선택(존재 시 RFM 집계 후 merge). Phase 5에서 실제 CSV에 맞게 상수 조정.
2. **전처리 `normalize`**: 원본 유지, `{col}_scaled` 컬럼 추가. in-place 덮어쓰기 없음.
3. **SCM 폴백 정책**: 그룹 행 수 60 미만 또는 Prophet 예외 시 ARIMA(1,1,1); ARIMA도 실패 시 해당 그룹 스킵(warning 로그), 나머지 그룹은 정상 반환.
4. **Dify 응답 매핑**: `data.outputs.answer` 경로 기준. self-hosted 버전에 따라 다를 수 있으므로 `agent_service.py` 매핑부만 조정하면 전체 변경 최소화 가능.
5. **`routing_service.route`의 `db` 인자**: Phase 5 연동 전까지 `_` 처리. Phase 5 DB-연동 경로(예: `compute_churn_risk`) 추가 시 직접 사용.
6. **docker-compose 3원 분리**: dev(15432/6379) · test(15433/6380) · prod(내부 포트). Dify prod(5433)와도 충돌 없음.

**테스트 결과**: `pytest idr_analytics/tests/unit/` → **123 passed, 0 failed** (2026-03-26). `ruff` / `mypy --strict` (39 source files) 통과.

**특이사항**:
- `crm_service._sync_churn_pipeline` 내부 `datetime.utcnow()` DeprecationWarning 2건 — 기능 영향 없음. Phase 5 이전에 `datetime.now(UTC)`로 교체 예정.
- `routing_service.route` TREND/AGGREGATION 분기에서 `asyncio.to_thread` 사용(lambda 래핑) — `bi_service`의 동기 메서드를 이벤트 루프 블로킹 없이 호출.
- 다음 세션: Phase 5 API 라우터 계층 (`auth`, `datasets`, `scm`, `crm`, `bi`, `agent`). **엔드포인트 파일에서 `from __future__ import annotations` 금지** (backend_architecture.md §1).

### [2026-03-26] Session 05 — Phase 5 API 라우터 + Gate C/D 통합 테스트 (plan.md Phase 5)

**완료 내용**: v1 라우터 전 구간(`auth`~`agent`)·ARQ 워커(`forecast`/`cluster`/`trend`)·`main` lifespan·통합 테스트 11건·비밀번호 검증을 `bcrypt` 네이티브로 전환(passlib/bcrypt4 초기화 이슈 회피).

**변경 파일** (주요):
- `idr_analytics/app/main.py`, `app/api/v1/api.py`, `app/api/v1/endpoints/*.py`, `app/workers/arq_worker.py`, `app/core/security.py`, `app/core/job_poll.py`, `app/core/config.py`, 서비스·스키마 보강
- `idr_analytics/tests/integration/conftest.py`, `helpers.py`, `test_api_phase5.py`
- `pyproject.toml` — dev `asgi-lifespan`, 직접 의존 `bcrypt ^4`, `poetry.lock`
- `docker-compose.test.yml` — `POSTGRES_PASSWORD` 기본값 `idr-test-pw`
- `docs/plans/plan.md` — Phase 5·7-3 체크 반영, 진행 표 갱신
- `docs/CURRENT_WORK_SESSION.md` — Gate C/D/E 반영 후 Session 06으로 교체

**결정 사항**:
1. **통합 테스트 lifespan**: httpx 0.27은 `ASGITransport(lifespan=…)` 미지원 → `asgi-lifespan.LifespanManager`로 감쌈.
2. **ARQ**: 엔드포인트 검증은 `create_pool` 목으로 Redis·워커 없이 `enqueue_job`만 확인.
3. **CRM 픽스처 CSV**: KMeans `n_clusters=4`보다 고객(행) 수가 많도록 최소 5고객·6행 샘플 유지.
4. **`security.verify_password`**: `bcrypt.checkpw` 단일 경로. `hash_password` 추가(시드·통합 테스트 공용).

**테스트 결과**: 단위 123 passed; 통합 11 passed (`POSTGRES_PASSWORD=idr-test-pw`, `make migrate-test`, 테스트 스택 기준). `ruff` / `mypy --strict` 통과.

**특이사항**: 기존 Postgres 볼륨에 다른 비밀번호가 박혀 있으면 `podman-compose … down -v` 후 재기동 또는 환경 변수를 볼륨 생성 시점과 맞출 것.

### [2026-03-26] Session 06 마감 — Phase 6 Dify 인프라·연동 + Gate D/E (plan.md Phase 6)

**완료 내용**: Dify 1.13.2 스택(`infra/dify/vendor` + `docker-compose.idr.yml`)·`make dify-*`·공개 프록시(한 도메인 path)·워크플로 DSL·Publish(수동). `plan.md` §「검증 시점」에 따라 **C-1/C-2(Dify API·Tier2 실연동)** 는 이연. **Gate D**: `make test`(단위 123·통합 11)·`make lint`·`make typecheck` 통과 후 `CURRENT` 기록. **Gate E**: 본 이력·`plan.md` 진행 표·`CURRENT` → Session 07(Phase 7) 전환.

**변경 파일** (누적·문서 중심; 구현 본문은 세션 전반에 분산):
- `infra/dify/*` — vendor 동기화, `docker-compose.idr.yml`, `README.md`, 워크플로 YAML, nginx·스크립트 등
- `Makefile` — `dify-up`/`dify-down`/JWT 보조 타겟
- `.env.example` / 루트 `.env`(로컬) — `DIFY_*` 안내
- `idr_analytics/app/core/config.py` — Dify URL 기본값 등
- `docs/CURRENT_WORK_SESSION.md` — Session 06 전 구간·Gate D 결과
- `docs/plans/plan.md` — Phase 6 체크·진행 표(본 Gate E 반영)

**결정 사항**:
1. **Dify 검증 시점**: HTTP Request·`workflows/run`·`/agent/query` Tier2 스모크는 루트 `.env`의 `DIFY_API_KEY`·`DIFY_WORKFLOW_ID` 실값 및 네트워크 전제와 함께 **Phase 7 통합·선택 E2E**에서 재검 (`plan.md` §Phase 6 표).
2. **회귀 검증**: Phase 6 종료 시점에 **C-3·품질 게이트**로 FastAPI 회귀를 확정(Gate D).

**테스트 결과 (Gate D, 2026-03-26)**: `make test` 통과(단위 123·통합 11); `ruff check`·`mypy idr_analytics/app --strict`(49 files) 통과. `podman-compose test` 기동/종료 시 dev/Dify와 네트워크·볼륨 공유로 **경고 로그**가 날 수 있으나 exit code 0.

**특이사항**: `plan.md` Phase 6의 **API Key → `.env` 실값** 체크박스(`Studio → API Key…`)는 운영자 `.env` 반영 여부에 따라 별도 완료 처리. 미반영 시 Tier2·C-1/C-2는 계속 블로커.

### [2026-03-27] Session 07 — Phase 7 §7-4 커버리지·pre-commit (plan.md Phase 7)

**완료 내용**: Gate A 계획 실행. `pytest --cov=app`가 `pytest-cov` 미설치로 실패하여 dev 의존성 추가 후 **단위 123·통합 11·합계 134** 전부 PASSED, **전체 `app` 커버리지 74%**, `htmlcov/` 생성(Git 무시). `pre-commit run --all-files`(ruff·ruff-format·mypy) 통과. `plan.md` §7-4 체크 완료 반영.

**변경 파일**:
- `pyproject.toml` — `[tool.poetry.group.dev.dependencies]` 에 `pytest-cov ^6.0`
- `poetry.lock` — `coverage`, `pytest-cov` 해상
- `docs/plans/plan.md` — §7-4 `[x]`, 진행 표·프로젝트 개요 문구
- `docs/CURRENT_WORK_SESSION.md` — Gate E: Session 08 템플릿으로 전환

**결정 사항**:
1. **§7-3 Phase 6 이연**(Dify `workflows/run`, Tier2 `/agent/query`)은 Gate A 범위에서 제외 유지 — 루트 `.env` `DIFY_*` 실값 전제 시 Session 08에서 재검.
2. 커버리지 합격선 수치는 미설정; 현황(74%)만 기록.

**테스트 결과 (Gate D, 2026-03-27)**: `make test-infra-up` → `make migrate-test` → `pytest idr_analytics/tests/unit/`·`integration/`·전체(위 명령) 통과. `datetime.utcnow()` DeprecationWarning 다수(기존 코드 경로). `arq_worker.py`는 통합에서 미실행으로 0% 커버(잔여).

**특이사항**: `podman-compose test-infra-up` 시 기존 pod/네트워크와 충돌 경고가 있을 수 있으나 최종적으로 `idr-postgres-test` healthy 확인.

