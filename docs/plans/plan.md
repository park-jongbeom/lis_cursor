# IDR 시스템 데이터 분석 AI 백엔드 — 전체 개발 계획서

> **기준 문서**: `ref_files/IDR_Data_Analysis_SDD.md` v1.1.0
> **아키텍처 규칙**: `docs/rules/project_context.md`, `docs/rules/backend_architecture.md`, `docs/rules/dify_integration.md`
> **작성일**: 2026-03-25

### Session 번호 정의

> **Session** = `CURRENT_WORK_SESSION.md` 단위로 진행되는 작업 묶음. Phase와 1:1이 아니며, 한 Phase에 여러 Session이 걸리거나 Phase 완료 후에도 운영 안정화 목적으로 계속될 수 있다.  
> 상세 이력은 `docs/history/WORK_HISTORY.md` 참조. 현재 세션 계획은 `docs/CURRENT_WORK_SESSION.md` 참조.

| Session | 날짜 | 주요 내용 | 연계 Phase |
|---------|------|----------|-----------|
| 01 | 2026-03-26 | Phase 0+1 스캐폴딩, 환경 분리, 최소 FastAPI | 0, 1 |
| 02 | 2026-03-26 | Phase 2 코어/DB (Config, ORM, Alembic, DI, Routing) | 2 |
| 03 | 2026-03-26 | Phase 3 Pydantic 스키마 DTO | 3 |
| 04 | 2026-03-26 | Phase 4 서비스·CRUD·단위 테스트 123건·테스트 DB | 4 |
| 05 | 2026-03-26 | Phase 5 API 라우터·ARQ 워커·통합 테스트 11건 | 5 |
| 06 | 2026-03-26 | Phase 6 Dify 인프라·워크플로 DSL·`make dify-*` | 6 |
| 07 | 2026-03-27 | Phase 7 커버리지·pre-commit (`pytest-cov` 추가) | 7 |
| 08 | 2026-03-27 | Phase 6/7 실연동 마무리(내부 우회 인증·Tier2 매핑·통합 13건) | 6, 7 |
| 09 | 2026-03-27 | 운영 안정화: Tier2 에러 분류 보강(`DIFY_INPUT_ERROR` 등) | post-7 |
| 10 | 2026-03-27 | 운영 안정화: 통합 환경 복구·`make test` 회귀 검증 | post-7 |
| 11 | 2026-03-27 | 운영 안정화: 테스트 compose `name: idr-test` 분리·`utcnow` 제거 | post-7 |
| 12 | 2026-03-27 | 운영 안정화: README·Makefile 테스트 가이드 정합성 | post-7 |
| 13 | 2026-03-27 | 운영 안정화: `env.example`·README `ALLOWED_ORIGINS` 형식·쉘 오염 주의 명시 | post-7 |
| 14 | 2026-03-27 | 운영 안정화: OpenAPI 보강·ARQ 잡 통합 테스트(`test_arq_worker_integration_suite`) | post-7 |
| 15 | 2026-03-27 | 운영 안정화: `0003_timestamptz`·운영 점검 `production_checklist.md` | post-7 |
| **16** | 2026-03-27 | **Gate E 완료** — Phase 9 데모(`demo/*`)·`env.example`·`make test` 134+15·이력 `WORK_HISTORY` 이전 | 9 |
| **17** | 2026-03-28 | **Gate E 완료** — pytest **152 passed**·샘플 CSV 통합·공인 `/ide` 계획 `CURRENT` 통합·데모 링크·`error_analysis`/remote-proxy 보강·ga-nginx 검증 기록(`WORK_HISTORY`) | 9 |
| **18** | 2026-03-28 | **Gate D 완료·Gate E(이력) 부분** — pytest **156 passed**·공인 스모크·`verify_dify_upstream`·Dify `DIFY_*` 문서·`CURRENT` 보충 테스트 계획·`WORK_HISTORY` 본 항목. **남음**: P9-1 UI·Tier2(`DIFY_*` 실환경)·`DEMO_SCRIPT`·Phase 9 최종 확정 | 9 |
| **19** | 2026-03-28 | **Gate E 완료** — `/ide/docs/rules/` **탭 UI**(Cursor·VS Code+Claude Code)·`make test` **156 passed**·TestClient·공인 `verify_lis_public_smoke`·`WORK_HISTORY`·`plan.md`·`CURRENT`→Session 20 교체 | 9 |

---

### 진행 현황 (Gate E 시 본 표·아래 Phase 체크박스 동기화)

| Phase | 상태 | 비고 |
|-------|:----:|------|
| 0 Pre-flight | 완료 | 도구 확인 (Session 01) |
| 1 Scaffolding | 완료 | `docker-compose.dev.yml` / `prod` 분리 등 (Session 01) |
| 2 코어/DB | 완료 | ORM, Alembic, routing, dependencies (Session 02) |
| 3 스키마 | 완료 | `app/schemas/*`, `test_schemas.py` (Session 03) |
| 4 서비스 | **완료** | 서비스·CRUD·단위 테스트 123개·테스트 DB 환경 (Session 04) |
| 5 API 라우터 | **완료** | v1 엔드포인트·ARQ 워커·통합 테스트 11건 (Session 05) |
| 6 Dify 인프라·연동 | 완료 | `DIFY_*` 실값 반영, `workflows/run`·Tier2 실연동 검증 완료 (Session 06·08) |
| 7 테스트·검증 | 완료 | §7-3(통합 확장) + §7-4(커버리지·pre-commit) 완료 (Session 07·08) |
| **운영 안정화** | **진행 중** | Phase 7 이후 후속 개선 — Session 09~15 완료, 이후는 Session 16+ (`plan.md` §Phase 8) |
| **강의 데모 UI** | **진행 중** | Session 19 마감 — 공인 **`/ide/docs/rules/`** 교육 탭 HTML·회귀 완료. **남음**: P9-1 브라우저·Dify Studio·`DEMO_SCRIPT`·Tier2 `DIFY_*`·Phase 9 확정 — **`CURRENT` Session 20** |

---

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **서비스명** | `idr_analytics` — IDR 시스템 데이터 분석 AI 에이전트 백엔드 |
| **현재 상태** | Phase 7 완료 + Phase 9 진행 중 — **`docs/CURRENT_WORK_SESSION.md` Session 20** (`make test` **156 passed**, 2026-03-28). Session 19에서 **`/ide/docs/rules/`** 탭(교육생 Cursor·VS Code+Claude)·회귀·공인 스모크 완료. **남음**: P9-1·`DEMO_SCRIPT`·Dify 육안·Tier2 `DIFY_*`(공인 `agent/query` 등) |
| **런타임** | RHEL 8 + rootless podman-compose / 호스트 miniconda Python 3.13 |
| **핵심 패턴** | 2-Tier 하이브리드 라우팅 (Pandas Tier 1 vs Dify+LLM Tier 2) |

### 3가지 비즈니스 목표

| # | 도메인 | 목표 | 기법 | 엔드포인트 |
|---|--------|------|------|-----------|
| BG-1 | SCM | 시약·키트 수요 예측 | Prophet / ARIMA | `/api/v1/scm/` |
| BG-2 | CRM | 거래처 이탈 감지 + 클러스터링 | K-Means / RFM | `/api/v1/crm/` |
| BG-3 | BI | 지역·시기별 질환 트렌드 분석 | GroupBy Pivot + LLM 요약 | `/api/v1/bi/` |

### 아키텍처 다이어그램 (간략)

```
Client / Dify Chat UI
    │
    ▼
FastAPI :8000   (CSV 수신 + Pandas 전처리 + SCM/CRM/BI 분석)
    │ Tier 1 (complexity < 70)     │ Tier 2 (complexity >= 70)
    ▼                              ▼
SCMService / CRMService / BIService    Dify :80 → LLM Node (Claude/Ollama)
    │                                      │ HTTP Request Node → FastAPI (compact=true)
    ▼                              ▼
PostgreSQL(호스트 매핑 예: 15432) / Redis :6379
```

---

## Phase 0 — Pre-flight 확인

> 참조: `docs/rules/project_context.md §실행환경`

- [x] 호스트 Python 버전 확인 (`/home/lukus/miniconda3/bin/python --version` → 3.13.x)
- [x] Poetry 설치 여부 확인 (`poetry --version`)
- [x] podman-compose 설치 여부 확인 (`podman-compose --version`)
- [x] pre-commit 설치 여부 확인 (`pre-commit --version`)

---

## Phase 1 — Scaffolding & 환경 세팅

> 참조: `docs/rules/project_context.md §디렉토리구조`, `docs/rules/backend_architecture.md §5`, SDD §6, §10

### 1-1. 의존성 및 품질 게이트

- [x] `pyproject.toml` 작성 (참조: SDD §10.3)
  - `[tool.poetry.dependencies]`: `fastapi ^0.115`, `sqlalchemy[asyncio] ^2.0`, `alembic ^1.14`, `asyncpg ^0.30`, `pydantic-settings ^2.0`, `arq ^0.26`, `pandas ^2.2`, `numpy ^1.26`, `prophet ^1.1`, `statsmodels ^0.14`, `scikit-learn ^1.5`, `langchain ^0.3`, `langchain-anthropic ^0.3`, `anthropic ^0.40`, `httpx ^0.27`, `redis ^5.0`, `python-multipart`, `python-jose[cryptography]`, `passlib[bcrypt]`
  - `[tool.poetry.group.dev.dependencies]`: `pytest ^8.0`, `pytest-asyncio ^0.24`, `ruff ^0.6`, `mypy ^1.11`
  - `[tool.ruff]`: `line-length = 120` (참조: `backend_architecture.md §5`)
  - `[tool.ruff.lint.per-file-ignores]`: `app/models/**` + `app/schemas/**` → `TCH003` 무시, `alembic/**` → `E501`, `TCH` 무시
  - `[tool.mypy]`: `strict = true`

- [x] `.pre-commit-config.yaml` 작성 (`ruff`, `mypy` 훅 등록)
- [x] `poetry install` 실행

### 1-2. 환경 변수

- [x] **`env.example`** 작성 (참조: SDD §10.1, `dify_integration.md §5`; `.env*` 는 Git 무시)
  - 필수 항목: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `AI_ESCALATION_THRESHOLD=70`, `PANDAS_MAX_ROWS=2000000`, `ANTHROPIC_API_KEY`, `LLM_MODEL=claude-sonnet-4-6`, `DIFY_API_BASE_URL`, `DIFY_API_KEY`, `DIFY_WORKFLOW_ID`, `PROPHET_CHANGEPOINT_SCALE=0.05`, `KMEANS_DEFAULT_CLUSTERS=4`, `CHURN_RECENCY_THRESHOLD_DAYS=90`
- [x] `.env` 작성 (`cp env.example .env` 후 실제 값) — 로컬 전용, Git 제외

### 1-3. 디렉토리 구조 생성

- [x] SDD §6 구조대로 `idr_analytics/` 전체 디렉토리 트리 및 `__init__.py` 생성
  ```
  idr_analytics/
  ├── app/
  │   ├── api/v1/endpoints/
  │   ├── core/
  │   ├── db/
  │   ├── models/
  │   ├── schemas/
  │   ├── services/data/
  │   ├── services/analytics/
  │   ├── services/ai/
  │   ├── crud/
  │   └── workers/
  ├── alembic/versions/
  ├── data/
  ├── notebooks/
  └── tests/unit/ tests/integration/
  ```

### 1-4. 인프라 컨테이너

- [x] 인프라 Compose 작성 (참조: SDD §10.2, `dify_integration.md §5`) — `docker-compose.dev.yml` / `docker-compose.prod.yml` 등 Session 01 구성
  - 로컬 Postgres 호스트 포트 **15432** 매핑(기존 5432 점유 회피), Redis 6379, 네트워크 `idr-net`
  - postgres healthcheck: `pg_isready` 등
- [x] 로컬에서 PG/Redis 기동·healthy 확인 (Session 01)

---

## Phase 2 — 코어/DB 계층 구현

> 참조: `docs/rules/backend_architecture.md §1, §3`, SDD §9

### 2-1. Config & Settings

- [x] `app/core/config.py` — `Pydantic BaseSettings` (참조: `backend_architecture.md §1`)
  - 모든 env var 필드 정의 (Phase 1-2 항목 전체)
  - `model_config = SettingsConfigDict(env_file=".env")`

### 2-2. DB 세션

- [x] `app/db/base.py` — `DeclarativeBase`
- [x] `app/db/session.py` — `create_async_engine` + `async_session_factory` + `get_db()`
  - 반환 타입 `AsyncGenerator[AsyncSession, None]` 명시 필수 (참조: `backend_architecture.md §1`)

### 2-3. ORM 모델

- [x] `app/models/user.py` — `User` (구현 필드: `id`, `username`, `hashed_password`, `role`, `is_active` 등 — SDD와 명칭 일부 상이 가능)
- [x] `app/models/dataset.py` — `AnalysisDataset` (참조: SDD §9.1)
  - `id: Mapped[uuid.UUID]`, `name`, `dataset_type`, `file_path`, `row_count`, `columns_json: JSONB`, `profile_json: JSONB`, `owner_id: FK(users.id)`
- [x] `app/models/analysis_result.py` — `AnalysisResult` + `InsightBlock` (참조: SDD §9.2)
  - `AnalysisResult`: `dataset_id`, `analysis_type`, `route_used`, `status`, `result_json: JSONB`, `complexity_score`, `processing_time_ms`
  - `InsightBlock`: `result_id`, `block_type`, `content: JSONB`, `source`, `confidence`

### 2-4. Alembic 마이그레이션

- [x] `alembic init` + `idr_analytics/alembic/env.py` async 설정
  - `run_migrations_online()` → `AsyncEngine` + `async_engine_from_config` 패턴
- [x] `alembic/versions/0001_initial_schema.py` — `users`, `analysis_datasets` 테이블
- [x] `alembic/versions/0002_analysis_results.py` — `analysis_results`, `insight_blocks` 테이블
  - Alembic downgrade에서 f-string SQL 절대 금지 → `sa.table().delete().where()` 패턴 (참조: `backend_architecture.md §5`)
- [x] `alembic upgrade head` 실행 확인 (환경별)

### 2-5. 의존성 주입 & 라우팅 코어

- [x] `app/core/dependencies.py` — `get_current_user`, `require_admin` (참조: `backend_architecture.md §3`)
  - `oauth2_scheme` → JWT 검증 → `User` 반환
  - SQLAlchemy WHERE 절: `true()` 사용 (`bool` 리터럴 금지, 참조: `backend_architecture.md §5`)
- [x] `app/core/routing.py` — `ComplexityScorer` (참조: SDD §5.2, `backend_architecture.md §2`)
  - `QueryType` enum: `AGGREGATION(10)`, `FORECAST(30)`, `CLUSTER(35)`, `TREND(25)`, `NATURAL_LANGUAGE(80)`, `ANOMALY_EXPLAIN(75)`
  - `DATA_SIZE_PENALTY`: `1_000_000 → +20`, `500_000 → +10`
  - `CROSS_TABLE_BONUS = 15`
  - `threshold`: `settings.AI_ESCALATION_THRESHOLD` (기본 70)

---

## Phase 3 — Pydantic 스키마(DTO) 계층

> 참조: SDD §7 (Request/Response 명세 전체)
> `app/schemas/**` → `from __future__ import annotations` 사용 가능

- [x] `app/schemas/dataset.py` — `DatasetUploadRequest`, `DatasetProfileResponse`
  - Response 필드: `dataset_id`, `dataset_name`, `row_count`, `columns`, `dtypes`, `null_counts`, `created_at`
- [x] `app/schemas/scm.py` — `ForecastRequest`, `ForecastResponse` 및 compact DTO
  - Request: `dataset_id`, `target_column`, `date_column`, `group_by`, `test_codes`, `forecast_days`, `model`
  - Response: `job_id`, `status`, `model_used`, `forecasts[{test_code, predictions[{ds, yhat, yhat_lower, yhat_upper}], trend_direction, seasonality}]`
- [x] `app/schemas/crm.py` — `ClusterRequest`, `ClusterResponse`, `ChurnRiskItem` 및 compact DTO
  - `ChurnRiskItem` 필드: `customer_code`, `customer_name`, `last_order_days_ago`, `churn_risk_score`, `rfm_segment`, `recommended_action`
- [x] `app/schemas/bi.py` — `TrendRequest`, `TrendResponse`, `HeatmapResponse` 및 compact DTO
  - `HeatmapResponse`: `period`, `test_category`, `heatmap[{region, order_count, yoy_growth, top_test}]`, `insight`
- [x] `app/schemas/agent.py` — `AgentQueryRequest`, `AgentQueryResponse`
  - Response: `session_id`, `query`, `answer`, `supporting_data`, `route_used`, `llm_model`, `processing_time_ms`

---

## Phase 4 — 서비스 계층 구현

> 참조: `docs/rules/backend_architecture.md §4 (Pandas 계층 분리)`, SDD §8

### 4-0. CRUD 계층 (서비스·엔드포인트보다 먼저)

Phase 4 서비스가 `dataset_id`로 DB에서 `AnalysisDataset`을 읽어야 하므로, **서비스 구현 전**에 다음을 둔다.

- [x] `app/crud/base.py` — Generic CRUD (`get`, `get_multi`, `create`, `update`, `delete`) — async SQLAlchemy 2.0 패턴
- [x] `app/crud/crud_user.py` — `User` 조회 등 (`dependencies`는 현재 직접 `select` 사용 가능하나, 재사용·테스트를 위해 CRUD 권장)
- [x] `app/crud/crud_dataset.py` — `AnalysisDataset` get/list/create/update/delete
- [x] `app/crud/__init__.py` — 필요 시 re-export

### 4-1. 데이터 계층

- [x] `app/services/data/ingestion_service.py` — CSV → validated `DataFrame`
  - `read_csv_validated()`: 컬럼 존재 여부, dtype 캐스팅, `row_count` 반환
  - `df.copy()` 불변성 원칙 준수 (참조: `backend_architecture.md §4`)
  - DB 저장 시 `columns_json` 권장 구조: `{"columns": [str, ...], "dtypes": {col: str}, "null_counts": {col: int}}` — `DatasetProfileResponse`와 매핑 시 서비스에서 `profile_json` 병합 또는 `model_validate`용 dict 조립
- [x] `app/services/data/preprocessing_service.py` (참조: SDD §4.1 Preprocessing Layer)
  - `build_time_index(df, date_col)`: `pd.to_datetime` → `set_index` → `sort_index` → `ffill()`
  - `fill_missing(df)`: 도메인별 결측치 전략 (수치 → ffill, 범주 → 최빈값)
  - `add_lag_features(df, col, lags)`: lag 1/7/30 rolling window
  - `normalize(df, cols)`: `StandardScaler` fit_transform
  - **모든 메서드: `df = df.copy()` 후 새 DataFrame 반환. in-place 수정 금지**

### 4-2. 분석 계층

- [x] `app/services/analytics/scm_service.py` — `SCMService` (참조: SDD §8.1)
  - `async forecast(df, target_col, date_col, group_col, periods)` → `ForecastResult`
  - Prophet 입력: `ds`, `y` 컬럼 rename → `model.fit()` → `make_future_dataframe()` → `predict()`
  - ARIMA 폴백: 데이터 행 < 60 또는 Prophet 예외 발생 시 `statsmodels ARIMA(1,1,1)` 자동 전환
- [x] `app/services/analytics/crm_service.py` — `CRMService` (참조: SDD §8.2)
  - `build_rfm_features(df, reference_date)`: `groupby("customer_code").agg(recency, frequency, monetary)` → `pd.qcut` 1~5 점수
  - `cluster(rfm, n_clusters=4)`: `StandardScaler` → `KMeans(random_state=42, n_init="auto")` → 세그먼트 레이블 매핑
  - `compute_churn_risk(dataset_id, db)`: RFM 빌드 → 클러스터 → `at_risk` 필터 (recency > `CHURN_RECENCY_THRESHOLD_DAYS`)
- [x] `app/services/analytics/bi_service.py` — `BIService` (참조: SDD §8.3)
  - `regional_trend(df, period_col, region_col, value_col)`: `pivot_table` → YoY 성장률 계산
  - `yoy_comparison(df, year_col, value_col)`: 전년 대비 증감률
  - `top_tests(df, period, top_n)`: `groupby("test_code").sum().nlargest(top_n)`
- [x] `app/services/analytics/routing_service.py` — `AnalysisRoutingService` (참조: `backend_architecture.md §2`, SDD §5)
  - `ComplexityScorer.score(request)` → `Route.PANDAS` or `Route.AI`
  - Pandas 분기: `SCMService / CRMService / BIService` 직접 호출
  - AI 분기: `AgentService.analyze()` 위임

### 4-3. AI 오케스트레이션 계층

- [x] `app/services/ai/agent_service.py` — `AgentService` (참조: SDD §8.4 방식 A, `dify_integration.md §4`)
  - `async analyze(query, dataset_id)` → `httpx.AsyncClient.post(f"{DIFY_API_BASE_URL}/workflows/run")`
  - `headers: {"Authorization": f"Bearer {DIFY_API_KEY}"}`
  - `response_mode: "blocking"`, `timeout=120.0`
  - **Pandas 연산 이 계층에서 절대 금지** (참조: `backend_architecture.md §4`)

---

## Phase 5 — API 라우터 계층 구현

> **주의**: `app/api/v1/endpoints/*.py` 파일에서 `from __future__ import annotations` 사용 금지
> FastAPI Depends가 런타임 타입 resolve 실패 → 422 에러 발생 (참조: `backend_architecture.md §1`)
> 서비스 주입: 모듈 레벨 인스턴스 + `Depends(lambda: svc)` 패턴 (참조: `backend_architecture.md §3`)

### ARQ 잡 결과·폴링 전략 (필수 결정)

`GET /scm/forecast/{job_id}`, `GET /crm/cluster/{job_id}` 등은 잡 상태(`pending` / `running` / `completed` / `failed`)와 결과를 반환해야 한다.

- **기본 권장**: ARQ가 **Redis**에 job 결과를 저장 — 폴링 엔드포인트는 ARQ API(또는 래퍼)로 `job_id` 조회.
- **장기 보관·감사**: 완료 시 `analysis_results`(및 `result_json`)에 스냅샷 저장을 **선택**으로 추가할 수 있다.
- 구현 시 `app/workers/arq_worker.py`와 엔드포인트가 동일한 직렬화 규칙을 쓰도록 문서화한다.

- [x] `app/main.py` — `FastAPI(lifespan=...)` + CORS + `api_router` 마운트
  - lifespan: DB 연결 풀 생성 / 종료
- [x] `app/api/v1/api.py` — `include_router` × 6 (`auth`, `datasets`, `scm`, `crm`, `bi`, `agent`)
- [x] `app/api/v1/endpoints/auth.py`
  - `POST /auth/login` → JWT 발급
  - `POST /auth/refresh` → 토큰 갱신
- [x] `app/api/v1/endpoints/datasets.py`
  - `POST /datasets/upload` — `UploadFile` + `multipart/form-data` → `ingestion_service` → DB 저장
  - `GET /datasets` — 목록 조회
  - `GET /datasets/{id}/preview` — 상위 20행
  - `GET /datasets/{id}/profile` — 데이터 품질 리포트
  - `DELETE /datasets/{id}`
- [x] `app/api/v1/endpoints/scm.py` (참조: SDD §7.3)
  - `POST /scm/forecast` — 비동기 ARQ job 등록 → `job_id` 반환
  - `GET /scm/forecast/{job_id}` — 폴링
  - `GET /scm/restock-alert?dataset_id=&compact=false`
  - `GET /scm/seasonal-pattern?dataset_id=&compact=false`
  - **`compact: bool = False` 파라미터 필수** (참조: `dify_integration.md §2`)
- [x] `app/api/v1/endpoints/crm.py` (참조: SDD §7.4, `dify_integration.md §2`)
  - `POST /crm/cluster` → ARQ job
  - `GET /crm/cluster/{job_id}`
  - `GET /crm/churn-risk?dataset_id=&top_n=20&compact=false`
  - `GET /crm/rfm-summary?dataset_id=&compact=false`
  - **compact=true 응답**: `high_risk_count`, `top_customers[{code,name,risk_score}][:top_n]`, `summary` (4KB 이하)
- [x] `app/api/v1/endpoints/bi.py` (참조: SDD §7.5, `dify_integration.md §2`)
  - `POST /bi/trend`
  - `GET /bi/trend/{job_id}`
  - `GET /bi/regional-heatmap?period=&test_category=&compact=false`
  - `GET /bi/yoy-comparison?dataset_id=&compact=false`
  - `GET /bi/top-tests?period=&top_n=10&compact=false`
  - **compact=true 응답**: `period`, `top_regions`, `trending_tests`, `heatmap_highlights`, `summary` (4KB 이하)
- [x] `app/api/v1/endpoints/agent.py` (참조: SDD §7.6)
  - `POST /agent/query` — body `AgentQueryRequest` → **`RoutingRequest`(또는 `ComplexityScorer` 입력)** 로 변환하는 어댑터(필드 매핑·기본 `query_type` 등) 후 `AnalysisRoutingService` / `ComplexityScorer.score()` → Tier 2 시 `AgentService.analyze()`
  - `GET /agent/query/{session_id}`
- [x] `app/workers/arq_worker.py` — ARQ `WorkerSettings` + `forecast_job`, `cluster_job`, `trend_job` (위 ARQ 결과 전략과 일치)

---

## Phase 6 — Dify Self-hosted 인프라 & 연동

> 참조: SDD §4.3, §10.2, `docs/rules/dify_integration.md §5`

- [x] `infra/dify/vendor` — Dify **v1.13.2** 공식 `docker/` 동기화 + `docker-compose.idr.yml` (Podman·`idr-net`·Postgres `15434`)
  - 스택: `api`, `worker`, `worker_beat`, `web`, `db_postgres`, `redis`, `sandbox`, `plugin_daemon`, `ssrf_proxy`, `nginx`, `weaviate`, `init_permissions` (공식 compose 기준)
  - 로컬 UI: **`EXPOSE_NGINX_PORT=8080`** (`infra/dify/.env`)
- [x] `make dify-up` / `podman-compose` 로 기동 (`infra/dify/README.md`)
- [x] Dify 콘솔 접속 → **관리자 계정 생성·로그인**
- [x] Settings → **Model Provider** 설정 (예: Ollama)
- [x] Studio → **API Key** 발급 → 루트 `.env`: `DIFY_API_KEY`, `DIFY_WORKFLOW_ID` (실값 반영 — Tier2·통합 검증 전 필수)
- [x] Dify Workflow 구성·DSL 가져오기 (참조: **`dify_integration.md` §3** — 동기 호출)
  ```
  Start → GET /crm/churn-risk?compact=true
        → GET /bi/regional-heatmap?compact=true&period=<필수>
        → Variable Aggregator → LLM → Answer
  ```
- [x] Workflow **Publish**(게시) 완료

### Phase 6 — Dify 검증 시점 (계획 조정)

워크플로 **게시까지는 완료**하였다. 다만 아래 항목은 **FastAPI 측 기본 기능(로그인·사용자·DB 시드 등)이 모두 구현·안정화된 뒤**, **즉시 수동 스모크로 강제하지 않고**, **통합 테스트 실행 시점**에 다시 점검한다.

| 이연 항목 | 비고 |
|-----------|------|
| Dify HTTP Request → FastAPI (`Bearer`, `host.containers.internal:8000` 등) | 로그인 발급 JWT·호스트 연결 전제 |
| Explore / `workflows/run` E2E | `DIFY_API_KEY`·`DIFY_WORKFLOW_ID`·시작 변수(`period` 등) 실환경 |
| FastAPI `POST /agent/query`(Tier2) 스모크 | `AgentService`·`.env`·위와 동일 전제 |
| Phase 7 통합 테스트 반영 | 기존 `test_api_phase5.py` 확장 또는 Dify Mock/선택적 E2E 시나리오로 재검 (세부는 Phase 7·`CURRENT_WORK_SESSION`에서 확정) |

---

## Phase 7 — 테스트 & 검증

> 참조: `docs/rules/backend_architecture.md §6`, SDD §부록B

### 7-1. 테스트 기반 설정

- [x] `idr_analytics/tests/conftest.py` — **파일 최상단에서 `os.environ.setdefault` 필수** (Phase 2에서 완료, 참조: `backend_architecture.md §6`)
  - 실제 프로젝트 URL은 **호스트 Postgres 포트 15432** 등 환경에 맞게 유지한다. Phase 7 예시의 `5433`은 참고용이며 복제 시 현재 `conftest.py`와 충돌하지 않도록 할 것.

### 7-2. 단위 테스트

> **동기화 (2026-03-26, Session 06→07 전환)**: 아래 파일·시나리오는 Phase 4~5에서 구현되었고 `make test` 단위 스위트(123건)에 포함됨. 추가 케이스는 Session 07 Gate A에서 정의.

- [x] `tests/unit/test_preprocessing_service.py`
  - `build_time_index()`: DatetimeIndex 생성 + ffill 확인
  - `add_lag_features()`: lag 컬럼 생성 확인
  - 원본 DataFrame 불변성 확인 (`id(original) != id(result)`)
- [x] `tests/unit/test_scm_service.py`
  - Prophet 수요 예측: 반환 컬럼 `[ds, yhat, yhat_lower, yhat_upper]` 존재 확인
  - ARIMA 폴백: 행 < 60 샘플 → ARIMA 실행 확인
- [x] `tests/unit/test_crm_service.py`
  - `build_rfm_features()`: `recency_score`, `frequency_score`, `monetary_score` 컬럼 확인
  - `cluster()`: `cluster` + `segment` 컬럼, `n_clusters` 개수 확인
- [x] `tests/unit/test_routing_service.py`
  - `AGGREGATION(10)` → Pandas Tier 1 라우팅 확인
  - `NATURAL_LANGUAGE(80)` → AI Tier 2 라우팅 확인
  - `FORECAST(30) + DATA_SIZE_PENALTY(20) + CROSS_TABLE_BONUS(15) = 65` → Tier 1 확인
- [x] `tests/unit/test_agent_service.py` — Dify httpx Mock (참조: `backend_architecture.md §6`)
  ```python
  with patch("app.services.ai.agent_service.httpx.AsyncClient") as mock_client:
      mock_response.json.return_value = {"data": {"outputs": {"answer": "분석 완료"}}}
  ```

### 7-3. 통합 테스트

- [x] `tests/integration/test_api_phase5.py` (+ `conftest.py`, `helpers.py`) — Phase 5 API 일괄 검증
  - `POST /scm/forecast` → 202 + `job_id` (ARQ `create_pool` 목)
  - `GET /scm/restock-alert?compact=true` → UTF-8 기준 4KB 이하
  - `GET /crm/churn-risk?compact=true` → `high_risk_count`, `top_customers`, `summary` 키
  - `GET /crm/churn-risk?compact=false` → `high_risk_customers` 등 전체 응답
  - 로그인·리프레시·소유권 403·미인증 401 등 포함 (`make test` / `POSTGRES_PASSWORD=idr-test-pw` + `migrate-test` 전제)
- [x] **Phase 6 연동(이연)**: Dify `workflows/run` 및 Tier2 `/agent/query` 실연동 검증 + 통합 테스트 확장 반영 (Session 08)

### 7-4. 최종 실행

> **Session 07 (2026-03-27)**: `--cov` 실행을 위해 dev 의존성 `pytest-cov` 추가(`pyproject.toml` / `poetry.lock`). HTML 리포트는 `htmlcov/`(Git 무시).

- [x] `PYTHONPATH=idr_analytics poetry run pytest idr_analytics/tests/ --cov=app --cov-report=term-missing` 전체 통과 확인
- [x] `pre-commit run --all-files` (ruff + mypy) 통과 확인

---

## Phase 8 — 운영 안정화 (post-Phase 7, 진행 중)

> **목적**: Phase 0~7 개발 완료 후 발생하는 운영·품질 개선 과제를 관리한다.  
> **참조**: 각 Session 이력은 `docs/history/WORK_HISTORY.md`, 현재 진행 계획은 `docs/CURRENT_WORK_SESSION.md`.

### 완료 항목 (Session 09~15)

- [x] Dify 업스트림 에러 코드 세분화 (`DIFY_INPUT_ERROR` / `DIFY_AUTH_ERROR` / `DIFY_TIMEOUT_ERROR`) — Session 09
- [x] `make test` 통합 환경 복구 및 Tier2 회귀 검증 완료 — Session 10
- [x] 테스트 compose `name: idr-test` 도입 — dev pod와 격리, Podman `Error:` 로그 제거 — Session 11
- [x] `datetime.utcnow()` 전면 제거 → `datetime.now(UTC).replace(tzinfo=None)` — Session 11
- [x] `README.md` 테스트 절차 갱신(`unset ALLOWED_ORIGINS`, `idr-test` 리소스, 레거시 정리) — Session 12
- [x] `Makefile` `test-infra-clean-legacy` 타깃 추가 — Session 12
- [x] `env.example` · `README.md`: `ALLOWED_ORIGINS` 형식(JSON 배열 문자열) 및 쉘 오염 주의 명시 — Session 13
- [x] Swagger/OpenAPI 태그·설명 보강 — Session 14
- [x] `arq_worker` 잡(`forecast`/`cluster`/`trend`) 통합 테스트 — Session 14 (`test_arq_worker_integration_suite`)
- [x] `created_at` 컬럼 `TIMESTAMP WITH TIME ZONE` 마이그레이션 (`0003_timestamptz`) — Session 15
- [x] 운영 환경(`APP_ENV=production`) 점검 체크리스트 — Session 15 (`docs/rules/production_checklist.md`)

### 후보 항목 (미착수 · Session 16+)

> 운영 중 발견되는 과제를 Gate A에서 목록에 추가·선택한다. (현재 `plan.md`에 고정 후보 없음.)

---

## Phase 9 — 강의 데모 UI (3/28 강의 발표용, post-Phase 8)

> **배경**: 2026-03-28(토) 김희원 강사 강의에서 보조강사로 이 프로젝트를 시연한다. 강사님의 이론 강의(4주차·5주차) + 데이터 분석 시연 후, 보조강사가 실제 동작하는 화면을 보여준다.  
> **강의 계획서 참조**: `ref_files/컨설팅계획서_김희원_IDR시스템즈_전문가_양식.md` — 4주차(AI 도구 기반 SW 개발 프로세스), 5주차(데이터 과학 AI 도구 활용), 6주차(분석 결과 비즈니스 기획)  
> **강사 지시**: "데이터분석 보여주고 → 밥먹고 → 코드 샘플 보여주고 → 보조강사가 한 거 보여주면"  
> **공인 URL 경로(강의·교육생 안내)**: 동일 호스트에서 **`/` = 데모**, **`/apps` = Dify**, **`/ide/…` = 규칙 가이드·ZIP** — 표·오해 제거는 **`docs/plans/lis_public_url_path_map.md`**.

---

### 현황 분석 — 지금 브라우저로 볼 수 있는 것

| 컴포넌트 | URL | 현재 상태 | 강의 가시성 |
|----------|-----|-----------|------------|
| FastAPI Swagger UI | `http://localhost:8000/docs` | ✅ 완성 | API 구조 설명은 가능하나 수치/차트 없음 |
| Dify Studio (워크플로 편집) | `http://localhost:8080` | ✅ 완성 | 워크플로 DSL 흐름 시각화 가능 |
| Dify Chat/Workflow 실행 화면 | `http://localhost:8080` — 앱 실행 페이지 | ✅ 이미 존재 | LLM 요약 결과 텍스트만 보임 |
| 분석 결과 시각화 UI | **없음** | ❌ 미구현 | 차트·표 없이 JSON만 반환 |
| 데이터 업로드 / 분석 실행 통합 화면 | **없음** | ❌ 미구현 | 청중이 직관적으로 이해하기 어려움 |

**결론**: Dify 워크플로 동작 자체는 브라우저에서 이미 시연 가능하나, **분석 결과를 시각적으로 보여주는 웹 UI**가 없다. 강의 시연을 위해 아래 두 트랙을 추가한다.

---

### 데모 시연 목표

| 단계 | 보여줄 내용 | 도구 |
|------|------------|------|
| ① Dify 워크플로 동작 | CRM 이탈 위험 + BI 트렌드 → LLM 요약이 Chat 창에 나타나는 장면 | Dify Studio `http://localhost:8080` |
| ② FastAPI Swagger 구조 | `/docs` — 엔드포인트 계층·`compact=true` 파라미터 설명 | `http://localhost:8000/docs` |
| ③ 데모 웹 UI (신규) | CSV 업로드 → 분석 실행 → 차트·표 시각화 (SCM/CRM/BI 한 화면) | 단일 HTML 페이지 |

---

### P9-1 : Dify 워크플로 시연 준비 (환경 점검)

> 코드 변경 없음 — 기동 상태·샘플 데이터 준비 체크리스트

- [ ] `make dify-up` 정상 기동 및 `http://localhost:8080` Studio 접근 확인
- [ ] `idr_crm_bi_tier2.yml` 워크플로가 Dify에 임포트되어 있고 **Publish** 상태인지 확인
- [ ] FastAPI 기동 (`PYTHONPATH=idr_analytics poetry run uvicorn app.main:app --reload --port 8000`) 및 `/health` 200 확인
- [ ] Dify HTTP 노드의 Bearer 토큰이 최신(만료 전)인지 확인 (`make dify-fastapi-jwt-bearer`)
- [ ] 부록 C의 Kaggle 대체 데이터셋 3종이 준비되어 있고, 미리 FastAPI에 업로드·등록까지 완료 (데모 중 로딩 딜레이 최소화)
- [ ] Dify Chat 앱에서 `user_query`+`dataset_id`+`period` 입력 → LLM 응답 정상 확인 (리허설)

**강의 시연 흐름 (Dify)**:

```
① Dify Studio → 워크플로 편집 화면 → 노드 구조 설명
   (시작 노드 → HTTP CRM → HTTP BI → 변수집계 → LLM → 종료)
② 앱 실행 창 → 입력값 입력 → 실행
③ LLM 요약 결과가 Chat 창에 스트리밍되는 장면 시연
```

---

### P9-2 : 데모 웹 UI 구축 (단일 HTML 파일 방식)

> **설계 원칙**:
> - 별도 프레임워크·빌드 불필요 — 단일 `demo/index.html` (CDN: Chart.js + Axios)
> - FastAPI 기존 엔드포인트를 그대로 호출 (`/api/v1/...`)
> - 강의용이므로 인증 간소화 — 개발용 `INTERNAL_BYPASS_BEARER_TOKEN`을 `.env`에 설정하고 HTML에 하드코딩 허용 (강의 노트북 전용, 프로덕션 배포 아님)
> - CORS: `ALLOWED_ORIGINS`에 `"http://localhost:5500"` 등 라이브 서버 포트 추가

#### 화면 구성

```
┌─────────────────────────────────────────────────────┐
│  IDR Analytics — AI 데이터 분석 데모                  │
├──────────────┬──────────────────────────────────────┤
│  [데이터 업로드] CSV 파일 선택 → 업로드 → dataset_id 표시 │
├──────────────┴──────────────────────────────────────┤
│  탭:  [SCM 수요예측] [CRM 이탈분석] [BI 트렌드]        │
│                                                     │
│  SCM 탭:                                            │
│   ├─ [예측 실행] 버튼 → POST /scm/forecast (ARQ 잡)  │
│   └─ Line Chart: 품목별 수요 예측 곡선 (Chart.js)     │
│                                                     │
│  CRM 탭:                                            │
│   ├─ [이탈 위험 분석] → GET /crm/churn-risk          │
│   ├─ Bar Chart: 이탈 위험 Top-N 거래처               │
│   └─ [클러스터 실행] → POST /crm/cluster (ARQ 잡)    │
│       └─ Scatter: RFM 세그먼트 분포                  │
│                                                     │
│  BI 탭:                                             │
│   ├─ [트렌드 분석] → GET /bi/regional-heatmap        │
│   ├─ Heatmap (지역 × 기간 매트릭스, Chart.js)        │
│   └─ [YoY 비교] → GET /bi/yoy-comparison            │
│       └─ Bar Chart: 전년 동기 대비                   │
│                                                     │
│  [Dify AI 요약] 버튼 → /agent/query Tier2 호출       │
│   └─ 텍스트 박스: LLM 한국어 요약 출력                │
└─────────────────────────────────────────────────────┘
```

#### 구현 체크리스트

- [x] `demo/index.html` 생성 (단일 파일 SPA)
  - Chart.js CDN + Axios CDN
  - 탭 구조 (SCM / CRM / BI + Agent)
  - CSV 업로드 → `POST /api/v1/datasets/upload` → `dataset_id` 저장
  - SCM: `POST /scm/forecast` → 잡 ID 폴링(`GET /scm/forecast/{job_id}`) → Line Chart 렌더
  - CRM: `GET /crm/churn-risk` → Bar Chart + `POST /crm/cluster` → 잡 폴링·표·세그먼트 막대
  - BI: `GET /bi/regional-heatmap` → 표·막대 + `GET /bi/yoy-comparison` → Bar Chart
  - [Dify AI 요약] 버튼 → `POST /agent/query` (Tier 2 경로) → 응답 텍스트 표시
- [x] `env.example`에 Live Server 출처 예시 반영 — 로컬 `.env`는 사용자가 직접 설정
- [ ] `.env` `INTERNAL_BYPASS_ENABLED=true` + `INTERNAL_BYPASS_BEARER_TOKEN=…` (.git 제외 — 강의 노트북 한정)
- [x] `demo/README.md` — 실행·CORS·우회·ARQ 워커·`admin` 시드

---

### P9-3 : 강의 당일 시연 순서 스크립트

> 강의 흐름과 연동한 시연 순서 — `demo/DEMO_SCRIPT.md`로 저장

```markdown
## 강의 시연 순서 (3/28 보조강사 파트)

### [오전] 4주차 — AI 도구 기반 소프트웨어 개발 프로세스

1. Cursor IDE + AI 작성 코드 구조 설명 (5분)
   - `.cursorrules`, `docs/plans/plan.md`, Gate A~E 워크플로 소개
   - "바이브코딩 vs 스펙 기반 개발" 대비 시연

2. FastAPI Swagger UI 구조 설명 (5분)
   - `http://localhost:8000/docs`
   - SCM / CRM / BI / Agent 엔드포인트 계층 설명
   - `compact=true` 파라미터 역할 시연

### [오후] 5주차+6주차 — 데이터 분석 + 비즈니스 AI 연동

3. 데모 웹 UI 시연 (10분)
   - `demo/index.html` 열기 (VS Code Live Server 또는 직접 파일 열기)
   - CSV 업로드 → SCM 수요 예측 차트
   - CRM 이탈 위험 거래처 Bar Chart
   - BI 지역별 질환 트렌드 Heatmap

4. Dify 워크플로 시연 (10분)
   - `http://localhost:8080` Studio — 노드 구조 설명
   - 앱 실행 → 입력 → LLM 요약 텍스트 스트리밍
   - "[Dify AI 요약] 버튼"으로 데모 UI에서도 동일 결과 재현
```

- [x] `demo/DEMO_SCRIPT.md` 작성 (위 내용 기반, 강의 날 직전 리허설 체크리스트 포함)

---

### Phase 9 완료 기준

| 항목 | 기준 |
|------|------|
| P9-1 환경 점검 | Dify `idr_crm_bi_tier2` 워크플로 실행 후 LLM 응답 확인 |
| P9-2 데모 UI | 브라우저에서 `demo/index.html` 열고 SCM·CRM·BI 3개 탭 차트 렌더 확인 |
| P9-3 스크립트 | `demo/DEMO_SCRIPT.md` 존재, 강의 당일 리허설 완료 |
| 전체 | `make dev-up` → uvicorn 기동 → `demo/index.html` → 차트 정상 표시 |

---

### Phase 9 위치 (Session 번호)

| Session | 내용 | 연계 |
|---------|------|------|
| 16 | P9-2 `demo/index.html`·README·P9-3 `DEMO_SCRIPT.md`·`env.example` + Gate A~E | Phase 9 |
| 17 | P9-1·pytest·샘플 CSV·공인 `/ide` 문서·Gate E | Phase 9 |
| 18 | P9-1 브라우저 나머지·리허설·공인 `/ide` Phase B·E·Phase 9 확정 | Phase 9 |
| 19 | `/ide/docs/rules/` 탭 UI·정본 동기화·pytest·공인 스모크·Gate E(`WORK_HISTORY`·`plan`·`CURRENT` 전환) | Phase 9 |

> 현재 세션: `docs/CURRENT_WORK_SESSION.md` **Session 20** — Phase 9 잔여(P9-1·Dify·`DEMO_SCRIPT`·Tier2).

---

## 부록 A. 핵심 아키텍처 규칙 레퍼런스

| 규칙 | 위치 | 요약 |
|------|------|------|
| `from __future__ import annotations` 금지 | `backend_architecture.md §1` | `endpoints/*.py` 파일 전체 적용. Depends 422 에러 원인 |
| `async/await` 일관성 | `backend_architecture.md §1` | 모든 엔드포인트/서비스 메서드는 `async def` |
| CPU-bound 동기 라이브러리 | `backend_architecture.md §1` | Prophet/sklearn 등은 `run_in_executor` 또는 ARQ 잡 |
| HTTP 에러 JSON | `backend_architecture.md §4` | Dify 파싱 가능한 `detail` 구조 권장 |
| `compact=true` 필수 | `dify_integration.md §2` | 모든 분석 엔드포인트. 응답 4KB 이하 |
| `df.copy()` 불변성 | `backend_architecture.md §4` | Pandas 계층. in-place 수정 금지 |
| conftest env var 선언 위치 | `backend_architecture.md §6` | `import os; os.environ.setdefault(...)` 파일 최상단 |
| SQLAlchemy `true()` | `backend_architecture.md §5` | WHERE 절에 Python `bool` 리터럴 금지 |
| Docker 네트워크 `idr-net` | `dify_integration.md §5` | FastAPI 스택 `name: idr-net`, Dify 스택 `external: true` |
| Ruff line-length | `backend_architecture.md §5` | `120` (한국어 주석 포함 시 88자 초과 빈번) |

## 부록 B. 포트 구성 요약

| 서비스 | 포트 | 비고 |
|--------|------|------|
| FastAPI (호스트 실행) | 8000 | uvicorn |
| PostgreSQL (idr) 컨테이너 내부 | 5432 | 표준 |
| PostgreSQL (idr) **호스트 매핑** | **15432** | 로컬 dev(`docker-compose.dev.yml` 등) — 기존 5432 점유 회피 |
| Redis | 6379 | idr 스택 |
| Dify Web UI + API | **8080** (호스트) | `infra/dify/` + `EXPOSE_NGINX_PORT` |
| PostgreSQL (Dify 전용) | **15434** (호스트) | `db_postgres` — idr DB(15432)와 분리 |
| Ollama (선택) | 11434 | 호스트 직접 실행 |

> 아키텍처 다이어그램의 `5432`는 **컨테이너 내부** 관점이다. 개발 PC에서 `psql`/pytest 연결 시에는 **호스트 포트(15432)** 를 사용한다.

## 부록 C. Kaggle 대체 데이터셋

| BG | 데이터셋 | 용도 | IDR 컬럼 매핑 |
|----|---------|------|---------------|
| BG-1 SCM | Store Sales - Time Series Forecasting | Prophet 수요 예측 실습 | `store_nbr→customer_code`, `family→test_code`, `date→order_date`, `sales→order_qty` |
| BG-2 CRM | Customer Churn Dataset | RFM + K-Means 클러스터링 실습 | `CustomerID→customer_code`, `MonthlyCharges→청구금액`, `Churn→해지여부` |
| BG-3 BI | Retail Store Inventory Forecasting Dataset | 지역별 트렌드 분석 실습 | `Region→region`, `Product→test_name_ko`, `Month→order_year_month` |
