# idr_analytics — IDR 시스템 데이터 분석 AI 백엔드

> LIS(유전자 검사 의뢰 관리) 정형 데이터를 AI로 분석해 비즈니스 의사결정을 자동화하는 FastAPI 백엔드
>  
> **현재 상태**: Phase 7 완료. Session 11에서 테스트 compose 프로젝트 분리(`name: idr-test`)·`make test` Podman 로그 정리·`utcnow` 제거 반영.

---

## 비즈니스 목표

| # | 도메인 | 목표 | AI 기법 | API 접두사 |
|---|--------|------|---------|-----------|
| BG-1 | **SCM** | 시약·키트 수요 예측 및 재고 최적화 | Prophet / ARIMA 시계열 예측 | `/api/v1/scm/` |
| BG-2 | **CRM** | 거래처 이탈 징후 감지·클러스터링 | K-Means / RFM 분석 | `/api/v1/crm/` |
| BG-3 | **BI** | 지역·시기별 질환 트렌드 분석 | GroupBy Pivot + LLM 요약 | `/api/v1/bi/` |

---

## 아키텍처 개요

```
Client / Dify Chat UI
        │
        ▼
FastAPI :8000
  - CSV 수신 / Pandas 전처리 / SCM·CRM·BI 분석
        │
   ComplexityScorer (0-100)
        │
   complexity < 70          complexity >= 70
        │                         │
        ▼                         ▼
Pandas Tier 1                 Dify Tier 2
(서비스 직접 분석)             (Workflow + LLM)
        │                         │
        ▼                         ▼
PostgreSQL / Redis           HTTP Request -> FastAPI ?compact=true
```

핵심 원칙:
- 2-Tier 하이브리드 라우팅(Tier 1: Pandas, Tier 2: Dify+LLM)
- Dify는 수치 계산을 하지 않고, FastAPI 결과 JSON을 해석
- 분석 API는 `compact=true` 응답을 제공해 LLM 컨텍스트 절약
- 엔드포인트·서비스 메서드는 async 일관성 유지

---

## 현재 구현 범위

완료된 항목(Phase 0~7):
- 프로젝트 스캐폴딩, 환경 분리(`dev`/`prod`/`test` compose)
- 코어/DB 계층(SQLAlchemy async, Alembic migration, DI, 라우팅 스코어러)
- 스키마 계층(Pydantic DTO: `datasets`, `scm`, `crm`, `bi`, `agent`)
- 서비스 계층(전처리, SCM/CRM/BI 분석, AgentService)
- API 라우터 계층(`/api/v1/auth|datasets|scm|crm|bi|agent`)
- Dify 인프라 연동(`infra/dify` 스택, `workflows/run` 연동 검증)
- 테스트/검증(단위·통합·커버리지·pre-commit 통과)

세부 진행 과제는 [`docs/CURRENT_WORK_SESSION.md`](docs/CURRENT_WORK_SESSION.md) 및 [`docs/plans/plan.md`](docs/plans/plan.md) 를 참고한다.

---

## 디렉토리 구조

```
/                               # 프로젝트 루트
├── idr_analytics/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/
│   │   │   ├── api.py
│   │   │   └── endpoints/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── crud/
│   │   └── workers/
│   ├── alembic/
│   └── tests/
├── docs/
├── infra/dify/
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── docker-compose.test.yml
├── Makefile
└── pyproject.toml
```

---

## 빠른 시작

```bash
# 1) 의존성 설치
poetry install

# 2) 환경 변수 준비 (템플릿 -> 로컬 파일)
cp env.example .env

# 3) 개발 인프라 기동 (PostgreSQL + Redis)
make dev-up

# 4) 마이그레이션
make migrate

# 5) 서버 실행
PYTHONPATH=idr_analytics poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger: `http://localhost:8000/docs`

---

## 테스트

```bash
# 단위 테스트
PYTHONPATH=idr_analytics poetry run pytest idr_analytics/tests/unit/ -v

# 전체(권장) — 쉘에 ALLOWED_ORIGINS가 잘못 설정되어 있으면 앱 Settings 로딩이 실패할 수 있어 unset 권장
unset ALLOWED_ORIGINS && make test
```

- **Podman**: `docker-compose.test.yml`에 compose 프로젝트명 **`idr-test`** 가 지정되어 있다. `make test`가 끝나면 `test-infra-down`이 컨테이너와 함께 **`idr-test_pgdata-test`** 볼륨·**`idr-test_idr-test-net`** 네트워크를 제거한다.
- **레거시**: Session 11 이전 스택에서 남은 **`lis_cursor_pgdata-test`** / **`lis_cursor_idr-test-net`** 은 `make test-infra-clean-legacy` 또는 수동 `podman volume rm` / `podman network rm` 으로 정리한다.

```bash
# 커버리지 리포트
PYTHONPATH=idr_analytics poetry run pytest idr_analytics/tests/ --cov=app --cov-report=term-missing
```

---

## 주요 Make 명령

```bash
# 코드 품질
make format
make lint
make typecheck

# 테스트
make test-unit
make test-unit-cov
make test
make test-infra-clean-legacy   # (선택) 구 테스트 볼륨/네트워크 lis_cursor_* 정리

# 인프라
make dev-up
make dev-down
make migrate
make migrate-test
```

---

## 환경 변수

`.env`로 시작하는 파일은 Git 추적 대상이 아닙니다.  
반드시 `env.example`(및 필요 시 `env.prod.example`, `infra/dify/env.vendor.example`)을 기준으로 로컬 파일을 생성해 사용하세요.

주요 변수:
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `ALLOWED_ORIGINS` — CORS용 **JSON 배열 문자열**(예: `["http://localhost:3000"]`). 쉘 환경 값이 잘못되면 Settings 오류가 날 수 있어, 전체 테스트 시 §테스트의 `unset ALLOWED_ORIGINS` 권장.
- `ANTHROPIC_API_KEY`
- `DIFY_API_BASE_URL`
- `DIFY_API_KEY`
- `DIFY_WORKFLOW_ID`

---

## 개발 로드맵

| Phase | 상태 |
|-------|:----:|
| 0 Pre-flight | 완료 |
| 1 Scaffolding | 완료 |
| 2 코어/DB | 완료 |
| 3 스키마 | 완료 |
| 4 서비스 | 완료 |
| 5 API 라우터 | 완료 |
| 6 Dify 인프라·연동 | 완료 |
| 7 테스트·검증 | 완료 |

세부 계획 및 현재 세션 진행 상태는 아래 문서를 참고합니다.
- `docs/plans/plan.md`
- `docs/CURRENT_WORK_SESSION.md`

---

## 기여·워크플로 규칙

- 게이트 워크플로: `docs/rules/workflow_gates.md`
- 백엔드 아키텍처 규칙: `docs/rules/backend_architecture.md`
- Dify 연동 규칙: `docs/rules/dify_integration.md`
- 프로젝트 컨텍스트/보안·ignore 규칙: `docs/rules/project_context.md`
- 커밋 메시지: 한국어 Conventional Commits (`feat(범위): 한글 제목`)

커밋 전 권장 순서:

```bash
make format && make lint && make typecheck
git add -A
git commit
```
