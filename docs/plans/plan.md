# IDR 시스템 데이터 분석 AI 백엔드 — 전체 개발 계획서

> **기준 문서**: `ref_files/IDR_Data_Analysis_SDD.md` v1.1.0
> **아키텍처 규칙**: `docs/rules/project_context.md`, `docs/rules/backend_architecture.md`, `docs/rules/dify_integration.md`
> **작성일**: 2026-03-25

---

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **서비스명** | `idr_analytics` — IDR 시스템 데이터 분석 AI 에이전트 백엔드 |
| **현재 상태** | 그린필드. `.cursorrules`, `docs/rules/`, `ref_files/` 만 존재. 코드 없음 |
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
PostgreSQL :5432 / Redis :6379
```

---

## Phase 0 — Pre-flight 확인

> 참조: `docs/rules/project_context.md §실행환경`

- [ ] 호스트 Python 버전 확인 (`/home/lukus/miniconda3/bin/python --version` → 3.13.x)
- [ ] Poetry 설치 여부 확인 (`poetry --version`)
- [ ] podman-compose 설치 여부 확인 (`podman-compose --version`)
- [ ] pre-commit 설치 여부 확인 (`pre-commit --version`)

---

## Phase 1 — Scaffolding & 환경 세팅

> 참조: `docs/rules/project_context.md §디렉토리구조`, `docs/rules/backend_architecture.md §5`, SDD §6, §10

### 1-1. 의존성 및 품질 게이트

- [ ] `pyproject.toml` 작성 (참조: SDD §10.3)
  - `[tool.poetry.dependencies]`: `fastapi ^0.115`, `sqlalchemy[asyncio] ^2.0`, `alembic ^1.14`, `asyncpg ^0.30`, `pydantic-settings ^2.0`, `arq ^0.26`, `pandas ^2.2`, `numpy ^1.26`, `prophet ^1.1`, `statsmodels ^0.14`, `scikit-learn ^1.5`, `langchain ^0.3`, `langchain-anthropic ^0.3`, `anthropic ^0.40`, `httpx ^0.27`, `redis ^5.0`, `python-multipart`, `python-jose[cryptography]`, `passlib[bcrypt]`
  - `[tool.poetry.group.dev.dependencies]`: `pytest ^8.0`, `pytest-asyncio ^0.24`, `ruff ^0.6`, `mypy ^1.11`
  - `[tool.ruff]`: `line-length = 120` (참조: `backend_architecture.md §5`)
  - `[tool.ruff.lint.per-file-ignores]`: `app/models/**` + `app/schemas/**` → `TCH003` 무시, `alembic/**` → `E501`, `TCH` 무시
  - `[tool.mypy]`: `strict = true`

- [ ] `.pre-commit-config.yaml` 작성 (`ruff`, `mypy` 훅 등록)
- [ ] `poetry install` 실행

### 1-2. 환경 변수

- [ ] `.env.example` 작성 (참조: SDD §10.1, `dify_integration.md §5`)
  - 필수 항목: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `AI_ESCALATION_THRESHOLD=70`, `PANDAS_MAX_ROWS=2000000`, `ANTHROPIC_API_KEY`, `LLM_MODEL=claude-sonnet-4-6`, `DIFY_API_BASE_URL`, `DIFY_API_KEY`, `DIFY_WORKFLOW_ID`, `PROPHET_CHANGEPOINT_SCALE=0.05`, `KMEANS_DEFAULT_CLUSTERS=4`, `CHURN_RECENCY_THRESHOLD_DAYS=90`
- [ ] `.env` 작성 (`.env.example` 기반, 실제 값 채우기)

### 1-3. 디렉토리 구조 생성

- [ ] SDD §6 구조대로 `idr_analytics/` 전체 디렉토리 트리 및 `__init__.py` 생성
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

- [ ] `docker-compose.yml` 작성 (참조: SDD §10.2, `dify_integration.md §5`)
  - 서비스: `fastapi :8000`, `postgres:15-alpine :5432`, `redis:7-alpine :6379`
  - 네트워크: `idr-net` (bridge, named — Dify가 external로 참조)
  - postgres healthcheck: `pg_isready -U idr`
- [ ] `podman-compose -f docker-compose.yml up -d` 실행 및 healthcheck 확인

---

## Phase 2 — 코어/DB 계층 구현

> 참조: `docs/rules/backend_architecture.md §1, §3`, SDD §9

### 2-1. Config & Settings

- [ ] `app/core/config.py` — `Pydantic BaseSettings` (참조: `backend_architecture.md §1`)
  - 모든 env var 필드 정의 (Phase 1-2 항목 전체)
  - `model_config = SettingsConfigDict(env_file=".env")`

### 2-2. DB 세션

- [ ] `app/db/base.py` — `DeclarativeBase`
- [ ] `app/db/session.py` — `create_async_engine` + `async_session_factory` + `get_db()`
  - 반환 타입 `AsyncGenerator[AsyncSession, None]` 명시 필수 (참조: `backend_architecture.md §1`)

### 2-3. ORM 모델

- [ ] `app/models/user.py` — `User` (`user_id`, `username`, `dept_code`, `role`, `is_active`)
- [ ] `app/models/dataset.py` — `AnalysisDataset` (참조: SDD §9.1)
  - `id: Mapped[uuid.UUID]`, `name`, `dataset_type`, `file_path`, `row_count`, `columns_json: JSONB`, `profile_json: JSONB`, `owner_id: FK(users.id)`
- [ ] `app/models/analysis_result.py` — `AnalysisResult` + `InsightBlock` (참조: SDD §9.2)
  - `AnalysisResult`: `dataset_id`, `analysis_type`, `route_used`, `status`, `result_json: JSONB`, `complexity_score`, `processing_time_ms`
  - `InsightBlock`: `result_id`, `block_type`, `content: JSONB`, `source`, `confidence`

### 2-4. Alembic 마이그레이션

- [ ] `alembic init alembic` 실행 + `alembic/env.py` async 설정
  - `run_migrations_online()` → `AsyncEngine` + `async_engine_from_config` 패턴
- [ ] `alembic/versions/0001_initial_schema.py` — `users`, `analysis_datasets` 테이블
- [ ] `alembic/versions/0002_analysis_results.py` — `analysis_results`, `insight_blocks` 테이블
  - Alembic downgrade에서 f-string SQL 절대 금지 → `sa.table().delete().where()` 패턴 (참조: `backend_architecture.md §5`)
- [ ] `alembic upgrade head` 실행 확인

### 2-5. 의존성 주입 & 라우팅 코어

- [ ] `app/core/dependencies.py` — `get_current_user`, `require_admin` (참조: `backend_architecture.md §3`)
  - `oauth2_scheme` → JWT 검증 → `User` 반환
  - SQLAlchemy WHERE 절: `true()` 사용 (`bool` 리터럴 금지, 참조: `backend_architecture.md §5`)
- [ ] `app/core/routing.py` — `ComplexityScorer` (참조: SDD §5.2, `backend_architecture.md §2`)
  - `QueryType` enum: `AGGREGATION(10)`, `FORECAST(30)`, `CLUSTER(35)`, `TREND(25)`, `NATURAL_LANGUAGE(80)`, `ANOMALY_EXPLAIN(75)`
  - `DATA_SIZE_PENALTY`: `1_000_000 → +20`, `500_000 → +10`
  - `CROSS_TABLE_BONUS = 15`
  - `threshold`: `settings.AI_ESCALATION_THRESHOLD` (기본 70)

---

## Phase 3 — Pydantic 스키마(DTO) 계층

> 참조: SDD §7 (Request/Response 명세 전체)
> `app/schemas/**` → `from __future__ import annotations` 사용 가능

- [ ] `app/schemas/dataset.py` — `DatasetUploadRequest`, `DatasetProfileResponse`
  - Response 필드: `dataset_id`, `dataset_name`, `row_count`, `columns`, `dtypes`, `null_counts`, `created_at`
- [ ] `app/schemas/scm.py` — `ForecastRequest`, `ForecastResponse`
  - Request: `dataset_id`, `target_column`, `date_column`, `group_by`, `test_codes`, `forecast_days`, `model`
  - Response: `job_id`, `status`, `model_used`, `forecasts[{test_code, predictions[{ds, yhat, yhat_lower, yhat_upper}], trend_direction, seasonality}]`
- [ ] `app/schemas/crm.py` — `ClusterRequest`, `ClusterResponse`, `ChurnRiskItem`
  - `ChurnRiskItem` 필드: `customer_code`, `customer_name`, `last_order_days_ago`, `churn_risk_score`, `rfm_segment`, `recommended_action`
- [ ] `app/schemas/bi.py` — `TrendRequest`, `TrendResponse`, `HeatmapResponse`
  - `HeatmapResponse`: `period`, `test_category`, `heatmap[{region, order_count, yoy_growth, top_test}]`, `insight`
- [ ] `app/schemas/agent.py` — `AgentQueryRequest`, `AgentQueryResponse`
  - Response: `session_id`, `query`, `answer`, `supporting_data`, `route_used`, `llm_model`, `processing_time_ms`

---

## Phase 4 — 서비스 계층 구현

> 참조: `docs/rules/backend_architecture.md §4 (Pandas 계층 분리)`, SDD §8

### 4-1. 데이터 계층

- [ ] `app/services/data/ingestion_service.py` — CSV → validated `DataFrame`
  - `read_csv_validated()`: 컬럼 존재 여부, dtype 캐스팅, `row_count` 반환
  - `df.copy()` 불변성 원칙 준수 (참조: `backend_architecture.md §4`)
- [ ] `app/services/data/preprocessing_service.py` (참조: SDD §4.1 Preprocessing Layer)
  - `build_time_index(df, date_col)`: `pd.to_datetime` → `set_index` → `sort_index` → `ffill()`
  - `fill_missing(df)`: 도메인별 결측치 전략 (수치 → ffill, 범주 → 최빈값)
  - `add_lag_features(df, col, lags)`: lag 1/7/30 rolling window
  - `normalize(df, cols)`: `StandardScaler` fit_transform
  - **모든 메서드: `df = df.copy()` 후 새 DataFrame 반환. in-place 수정 금지**

### 4-2. 분석 계층

- [ ] `app/services/analytics/scm_service.py` — `SCMService` (참조: SDD §8.1)
  - `async forecast(df, target_col, date_col, group_col, periods)` → `ForecastResult`
  - Prophet 입력: `ds`, `y` 컬럼 rename → `model.fit()` → `make_future_dataframe()` → `predict()`
  - ARIMA 폴백: 데이터 행 < 60 또는 Prophet 예외 발생 시 `statsmodels ARIMA(1,1,1)` 자동 전환
- [ ] `app/services/analytics/crm_service.py` — `CRMService` (참조: SDD §8.2)
  - `build_rfm_features(df, reference_date)`: `groupby("customer_code").agg(recency, frequency, monetary)` → `pd.qcut` 1~5 점수
  - `cluster(rfm, n_clusters=4)`: `StandardScaler` → `KMeans(random_state=42, n_init="auto")` → 세그먼트 레이블 매핑
  - `compute_churn_risk(dataset_id, db)`: RFM 빌드 → 클러스터 → `at_risk` 필터 (recency > `CHURN_RECENCY_THRESHOLD_DAYS`)
- [ ] `app/services/analytics/bi_service.py` — `BIService` (참조: SDD §8.3)
  - `regional_trend(df, period_col, region_col, value_col)`: `pivot_table` → YoY 성장률 계산
  - `yoy_comparison(df, year_col, value_col)`: 전년 대비 증감률
  - `top_tests(df, period, top_n)`: `groupby("test_code").sum().nlargest(top_n)`
- [ ] `app/services/analytics/routing_service.py` — `AnalysisRoutingService` (참조: `backend_architecture.md §2`, SDD §5)
  - `ComplexityScorer.score(request)` → `Route.PANDAS` or `Route.AI`
  - Pandas 분기: `SCMService / CRMService / BIService` 직접 호출
  - AI 분기: `AgentService.analyze()` 위임

### 4-3. AI 오케스트레이션 계층

- [ ] `app/services/ai/agent_service.py` — `AgentService` (참조: SDD §8.4 방식 A, `dify_integration.md §4`)
  - `async analyze(query, dataset_id)` → `httpx.AsyncClient.post(f"{DIFY_API_BASE_URL}/workflows/run")`
  - `headers: {"Authorization": f"Bearer {DIFY_API_KEY}"}`
  - `response_mode: "blocking"`, `timeout=120.0`
  - **Pandas 연산 이 계층에서 절대 금지** (참조: `backend_architecture.md §4`)

---

## Phase 5 — API 라우터 계층 구현

> **주의**: `app/api/v1/endpoints/*.py` 파일에서 `from __future__ import annotations` 사용 금지
> FastAPI Depends가 런타임 타입 resolve 실패 → 422 에러 발생 (참조: `backend_architecture.md §1`)
> 서비스 주입: 모듈 레벨 인스턴스 + `Depends(lambda: svc)` 패턴 (참조: `backend_architecture.md §3`)

- [ ] `app/main.py` — `FastAPI(lifespan=...)` + CORS + `api_router` 마운트
  - lifespan: DB 연결 풀 생성 / 종료
- [ ] `app/api/v1/api.py` — `include_router` × 5 (`auth`, `datasets`, `scm`, `crm`, `bi`, `agent`)
- [ ] `app/api/v1/endpoints/auth.py`
  - `POST /auth/login` → JWT 발급
  - `POST /auth/refresh` → 토큰 갱신
- [ ] `app/api/v1/endpoints/datasets.py`
  - `POST /datasets/upload` — `UploadFile` + `multipart/form-data` → `ingestion_service` → DB 저장
  - `GET /datasets` — 목록 조회
  - `GET /datasets/{id}/preview` — 상위 20행
  - `GET /datasets/{id}/profile` — 데이터 품질 리포트
  - `DELETE /datasets/{id}`
- [ ] `app/api/v1/endpoints/scm.py` (참조: SDD §7.3)
  - `POST /scm/forecast` — 비동기 ARQ job 등록 → `job_id` 반환
  - `GET /scm/forecast/{job_id}` — 폴링
  - `GET /scm/restock-alert?dataset_id=&compact=false`
  - `GET /scm/seasonal-pattern?dataset_id=&compact=false`
  - **`compact: bool = False` 파라미터 필수** (참조: `dify_integration.md §2`)
- [ ] `app/api/v1/endpoints/crm.py` (참조: SDD §7.4, `dify_integration.md §2`)
  - `POST /crm/cluster` → ARQ job
  - `GET /crm/cluster/{job_id}`
  - `GET /crm/churn-risk?dataset_id=&top_n=20&compact=false`
  - `GET /crm/rfm-summary?dataset_id=&compact=false`
  - **compact=true 응답**: `high_risk_count`, `top_customers[{code,name,risk_score}][:top_n]`, `summary` (4KB 이하)
- [ ] `app/api/v1/endpoints/bi.py` (참조: SDD §7.5, `dify_integration.md §2`)
  - `POST /bi/trend`
  - `GET /bi/trend/{job_id}`
  - `GET /bi/regional-heatmap?period=&test_category=&compact=false`
  - `GET /bi/yoy-comparison?dataset_id=&compact=false`
  - `GET /bi/top-tests?period=&top_n=10&compact=false`
  - **compact=true 응답**: `period`, `top_regions`, `trending_tests`, `heatmap_highlights`, `summary` (4KB 이하)
- [ ] `app/api/v1/endpoints/agent.py` (참조: SDD §7.6)
  - `POST /agent/query` → `AnalysisRoutingService.score()` → `AgentService.analyze()` (Dify 프록시)
  - `GET /agent/query/{session_id}`
- [ ] `app/crud/base.py` — Generic CRUD (`get`, `get_multi`, `create`, `update`, `delete`)
- [ ] `app/crud/crud_dataset.py` — `AnalysisDataset` CRUD
- [ ] `app/workers/arq_worker.py` — ARQ `WorkerSettings` + `forecast_job`, `cluster_job` 태스크 정의

---

## Phase 6 — Dify Self-hosted 인프라 & 연동

> 참조: SDD §4.3, §10.2, `docs/rules/dify_integration.md §5`

- [ ] `docker-compose.dify.yml` 작성 (참조: SDD §10.2)
  - 서비스: `api`, `worker`, `web`, `db(postgres:15 :5433)`, `sandbox`, `nginx(:80)`
  - 네트워크: `idr-net: external: true` — FastAPI 스택과 동일 네트워크 공유
  - `REDIS_HOST`: `idr-net`의 Redis 컨테이너 서비스명
- [ ] `podman-compose -f docker-compose.dify.yml up -d` 실행
- [ ] `http://localhost` 접속 → Dify 관리자 계정 생성 → API Key 발급
- [ ] `.env` 업데이트: `DIFY_API_KEY`, `DIFY_WORKFLOW_ID`
- [ ] Dify Workflow 에디터에서 CRM 이탈 분석 워크플로 구성 (참조: `dify_integration.md §3`)
  ```
  Start → HTTP Request (POST /crm/cluster?compact=true)
        → HTTP Request (GET /bi/regional-heatmap?compact=true)
        → Variable Aggregator
        → LLM Node (Claude Sonnet / System Prompt: 영업 분석 전문가)
        → Answer Node
  ```
- [ ] Dify Chat UI에서 자연어 쿼리 테스트: "이탈 위험 고객 분석해줘"

---

## Phase 7 — 테스트 & 검증

> 참조: `docs/rules/backend_architecture.md §6`, SDD §부록B

### 7-1. 테스트 기반 설정

- [ ] `tests/conftest.py` — **파일 최상단에서 `os.environ.setdefault` 필수** (참조: `backend_architecture.md §6`)
  ```python
  import os
  os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5433/idr_test")
  os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
  os.environ.setdefault("SECRET_KEY", "test-secret-key")
  os.environ.setdefault("AI_ESCALATION_THRESHOLD", "70")
  # 위 설정 이후 app.* import
  ```

### 7-2. 단위 테스트

- [ ] `tests/unit/test_preprocessing_service.py`
  - `build_time_index()`: DatetimeIndex 생성 + ffill 확인
  - `add_lag_features()`: lag 컬럼 생성 확인
  - 원본 DataFrame 불변성 확인 (`id(original) != id(result)`)
- [ ] `tests/unit/test_scm_service.py`
  - Prophet 수요 예측: 반환 컬럼 `[ds, yhat, yhat_lower, yhat_upper]` 존재 확인
  - ARIMA 폴백: 행 < 60 샘플 → ARIMA 실행 확인
- [ ] `tests/unit/test_crm_service.py`
  - `build_rfm_features()`: `recency_score`, `frequency_score`, `monetary_score` 컬럼 확인
  - `cluster()`: `cluster` + `segment` 컬럼, `n_clusters` 개수 확인
- [ ] `tests/unit/test_routing_service.py`
  - `AGGREGATION(10)` → Pandas Tier 1 라우팅 확인
  - `NATURAL_LANGUAGE(80)` → AI Tier 2 라우팅 확인
  - `FORECAST(30) + DATA_SIZE_PENALTY(20) + CROSS_TABLE_BONUS(15) = 65` → Tier 1 확인
- [ ] `tests/unit/test_agent_service.py` — Dify httpx Mock (참조: `backend_architecture.md §6`)
  ```python
  with patch("app.services.ai.agent_service.httpx.AsyncClient") as mock_client:
      mock_response.json.return_value = {"data": {"outputs": {"answer": "분석 완료"}}}
  ```

### 7-3. 통합 테스트

- [ ] `tests/integration/test_scm_endpoints.py`
  - `POST /scm/forecast` → 202 Accepted + `job_id` 반환 확인
  - `GET /scm/restock-alert?compact=true` → 응답 4KB 이하 확인
- [ ] `tests/integration/test_crm_endpoints.py`
  - `GET /crm/churn-risk?compact=true` → `high_risk_count`, `top_customers`, `summary` 키 존재 확인
  - `GET /crm/churn-risk?compact=false` → 전체 응답 반환 확인

### 7-4. 최종 실행

- [ ] `PYTHONPATH=. pytest tests/ --cov=app --cov-report=term-missing` 전체 통과 확인
- [ ] `pre-commit run --all-files` (ruff + mypy) 통과 확인

---

## 부록 A. 핵심 아키텍처 규칙 레퍼런스

| 규칙 | 위치 | 요약 |
|------|------|------|
| `from __future__ import annotations` 금지 | `backend_architecture.md §1` | `endpoints/*.py` 파일 전체 적용. Depends 422 에러 원인 |
| `async/await` 일관성 | `backend_architecture.md §1` | 모든 엔드포인트/서비스 메서드는 `async def` |
| `compact=true` 필수 | `dify_integration.md §2` | 모든 분석 엔드포인트. 응답 4KB 이하 |
| `df.copy()` 불변성 | `backend_architecture.md §4` | Pandas 계층. in-place 수정 금지 |
| conftest env var 선언 위치 | `backend_architecture.md §6` | `import os; os.environ.setdefault(...)` 파일 최상단 |
| SQLAlchemy `true()` | `backend_architecture.md §5` | WHERE 절에 Python `bool` 리터럴 금지 |
| Docker 네트워크 `idr-net` | `dify_integration.md §5` | FastAPI 스택 `name: idr-net`, Dify 스택 `external: true` |
| Ruff line-length | `backend_architecture.md §5` | `120` (한국어 주석 포함 시 88자 초과 빈번) |

## 부록 B. 포트 구성 요약

| 서비스 | 포트 | compose 파일 |
|--------|------|-------------|
| FastAPI | 8000 | `docker-compose.yml` |
| PostgreSQL (idr) | 5432 | `docker-compose.yml` |
| Redis | 6379 | `docker-compose.yml` |
| Dify Web UI + API | 80 | `docker-compose.dify.yml` |
| PostgreSQL (Dify) | 5433 | `docker-compose.dify.yml` |
| Ollama (선택) | 11434 | 호스트 직접 실행 |

## 부록 C. Kaggle 대체 데이터셋

| BG | 데이터셋 | 용도 | IDR 컬럼 매핑 |
|----|---------|------|---------------|
| BG-1 SCM | Store Sales - Time Series Forecasting | Prophet 수요 예측 실습 | `store_nbr→customer_code`, `family→test_code`, `date→order_date`, `sales→order_qty` |
| BG-2 CRM | Customer Churn Dataset | RFM + K-Means 클러스터링 실습 | `CustomerID→customer_code`, `MonthlyCharges→청구금액`, `Churn→해지여부` |
| BG-3 BI | Retail Store Inventory Forecasting Dataset | 지역별 트렌드 분석 실습 | `Region→region`, `Product→test_name_ko`, `Month→order_year_month` |
