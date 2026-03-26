# idr_analytics — IDR 시스템 데이터 분석 AI 백엔드

> LIS(유전자 검사 의뢰 관리) 정형 데이터를 AI로 분석해 비즈니스 의사결정을 자동화하는 FastAPI 백엔드.  
> **현재 상태**: Phase 4 완료 (서비스·CRUD·단위 테스트 123개) · Phase 5 API 라우터 계층 진행 예정

---

## 목차

- [비즈니스 목표](#비즈니스-목표)
- [아키텍처 개요](#아키텍처-개요)
- [기술 스택](#기술-스택)
- [디렉토리 구조](#디렉토리-구조)
- [빠른 시작](#빠른-시작)
- [개발 환경 설정](#개발-환경-설정)
- [주요 Make 명령](#주요-make-명령)
- [테스트](#테스트)
- [환경 변수](#환경-변수)
- [개발 로드맵](#개발-로드맵)
- [기여·워크플로 규칙](#기여워크플로-규칙)

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
FastAPI :8000                      ← CSV 수신 · Pandas 전처리 · 분석 실행
        │
   ComplexityScorer (0–100)
        │
   complexity < 70          complexity ≥ 70
        │                         │
        ▼                         ▼
SCMService / CRMService     Dify :80  (Self-hosted)
BIService  (Pandas)              │
        │                LLM Node (Claude / Ollama)
        │                         │ HTTP Request Node → FastAPI ?compact=true
        ▼                         ▼
PostgreSQL 15+  ·  Redis (ARQ 비동기 잡 큐 / 캐시)
```

### 핵심 설계 원칙

- **2-Tier 하이브리드 라우팅**: 단순 분석(Tier 1)은 Pandas로 직접, 복잡 질의(Tier 2)는 Dify 워크플로 → LLM으로 위임.
- **Dify는 수치 계산 금지**: 모든 집계·예측은 FastAPI/Pandas에서 완료 후 Dify에 정제된 JSON 전달.
- **`compact=true` 파라미터**: Dify HTTP Request Node가 LLM 컨텍스트 낭비 없이 핵심 필드만 수신.
- **모든 엔드포인트·서비스는 `async`**: SQLAlchemy 2.0 async, ARQ 비동기 잡 통합.

---

## 기술 스택

| 계층 | 기술 | 버전 | Spring Boot 대응 |
|------|------|------|-----------------|
| API Framework | **FastAPI** | ≥0.115 | @RestController |
| 데이터 처리 | **Pandas 2.x**, NumPy | ≥2.2 / ≥1.26 | Stream API + DTO |
| 시계열 예측 | **Prophet** (Meta), statsmodels ARIMA | ≥1.1 / ≥0.14 | Spring Batch |
| 클러스터링 | **scikit-learn** (K-Means, DBSCAN) | ≥1.5 | MLflow Pipeline |
| AI 오케스트레이션 | **Self-hosted Dify** | — | Camunda |
| LLM 클라이언트 | **Claude API** (anthropic), Ollama | ≥0.40 | OpenFeign |
| ORM | **SQLAlchemy 2.0** async | ≥2.0 | JPA + Hibernate |
| 마이그레이션 | **Alembic** | ≥1.14 | Flyway |
| 비동기 잡 큐 | **ARQ** (Redis-backed) | ≥0.26 | @Async |
| 캐시 / 큐 | **Redis** | ≥5.0 | Spring Cache |
| DB | **PostgreSQL** | ≥15 | — |
| HTTP 클라이언트 | **httpx** | ≥0.27 | WebClient |
| 컨테이너 | **rootless podman-compose** | — | Docker Compose |

---

## 디렉토리 구조

```
/                               ← 프로젝트 루트
├── idr_analytics/              ← Python 패키지 루트
│   ├── app/
│   │   ├── main.py             # FastAPI 앱 · lifespan
│   │   ├── api/v1/
│   │   │   ├── api.py          # 라우터 통합
│   │   │   └── endpoints/      # auth · datasets · scm · crm · bi · agent
│   │   ├── core/
│   │   │   ├── config.py       # Pydantic Settings
│   │   │   ├── dependencies.py # FastAPI Depends (DB · Auth)
│   │   │   └── routing.py      # ComplexityScorer
│   │   ├── db/                 # session · base
│   │   ├── models/             # SQLAlchemy ORM
│   │   ├── schemas/            # Pydantic DTO
│   │   ├── services/
│   │   │   ├── data/           # ingestion_service · preprocessing_service
│   │   │   ├── analytics/      # scm · crm · bi · routing_service
│   │   │   └── ai/             # agent_service (Dify 프록시)
│   │   ├── crud/               # CRUDBase · datasets · users
│   │   └── workers/            # arq_worker.py
│   ├── alembic/
│   └── tests/
│       ├── unit/               # 123개 단위 테스트
│       └── integration/
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── docker-compose.test.yml
├── Makefile
├── pyproject.toml
├── docs/                       # 계획서 · 규칙 · 이력
└── ref_files/                  # IDR_Data_Analysis_SDD.md
```

---

## 빠른 시작

> **전제**: RHEL 8 / CentOS Stream 8 · rootless podman-compose · Python ≥3.12 · Poetry

```bash
# 1. 의존성 설치
poetry install

# 2. 개발 인프라 기동 (PostgreSQL + Redis)
make dev-up

# 3. 환경 변수 설정 (`.env*` 파일은 Git 무시 — 템플릿은 env.example)
cp env.example .env
# .env 편집: DATABASE_URL, REDIS_URL, SECRET_KEY, ANTHROPIC_API_KEY 등

# 4. DB 마이그레이션
make migrate

# 5. 서버 실행
PYTHONPATH=idr_analytics poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI: `http://localhost:8000/docs`

---

## 개발 환경 설정

### 실행 환경 고정 사항

| 항목 | 값 |
|------|-----|
| OS | RHEL 8 (kernel 4.18.0) |
| 컨테이너 | rootless podman / podman-compose (Docker CLI 호환) |
| SELinux | Enabled |
| Python (호스트) | miniconda 3.13.x |
| ruff · mypy · pytest | 호스트 miniconda에서 직접 실행 |

> RHEL 8 + rootless podman + SELinux 환경에서 컨테이너 내 `apt-get` 빌드 시 glibc RELRO 충돌이 발생합니다. 따라서 **품질 도구(ruff · mypy · pytest)는 호스트에서** 실행합니다.

### pre-commit 설치

```bash
poetry run pre-commit install
```

커밋 전 자동으로 `ruff check`·`ruff format`·`mypy --strict` 가 실행됩니다.

> **주의**: unstaged 파일이 있으면 pre-commit stash 후 훅 수정이 롤백될 수 있습니다.  
> 커밋 전 반드시 `make format && make lint && make typecheck` → `git add -A` 순서를 지키세요.

---

## 주요 Make 명령

```bash
# 코드 품질
make format        # ruff format (자동 포맷)
make lint          # ruff check
make typecheck     # mypy --strict

# 테스트
make test-unit     # 단위 테스트 (호스트 직접 실행)
make test-unit-cov # 커버리지 포함
make test          # 전체: 인프라 기동 → 마이그레이션 → 단위+통합 → 인프라 종료

# 인프라
make dev-up        # 개발 인프라 기동 (PostgreSQL + Redis)
make dev-down      # 개발 인프라 종료
make migrate       # Alembic 마이그레이션 (개발 DB)
make migrate-test  # Alembic 마이그레이션 (테스트 DB)
```

---

## 테스트

```bash
# 단위 테스트 (인프라 불필요)
PYTHONPATH=idr_analytics poetry run pytest idr_analytics/tests/unit/ -v

# 통합 테스트 (PostgreSQL + Redis 필요)
make test-infra-up
make migrate-test
PYTHONPATH=idr_analytics poetry run pytest idr_analytics/tests/integration/ -v
```

| 구분 | 현황 |
|------|------|
| 단위 테스트 | **123개 통과** (Phase 4 기준) |
| 통합 테스트 | Phase 5+ 진행 예정 |

---

## 환경 변수

루트 **`env.example`** 을 **`cp env.example .env`** 로 복사해 사용합니다. (이름이 `.env`로 시작하는 파일은 `.gitignore`로 전부 제외)

| 변수 | 설명 | 예시 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL async URL | `postgresql+asyncpg://idr:pw@localhost:15432/idr` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT 서명 키 (32자 이상) | — |
| `ANTHROPIC_API_KEY` | Claude API 키 | `sk-ant-...` |
| `DIFY_API_KEY` | Dify API 키 | `app-...` |
| `DIFY_BASE_URL` | Self-hosted Dify URL | `http://localhost:80` |
| `DIFY_WORKFLOW_ID` | Dify 워크플로 ID | — |

---

## 개발 로드맵

| Phase | 내용 | 상태 |
|-------|------|:----:|
| 0 | Pre-flight (도구 확인) | ✅ |
| 1 | 스캐폴딩 · 환경 세팅 | ✅ |
| 2 | 코어·DB (ORM, Alembic, routing) | ✅ |
| 3 | 스키마 (Pydantic DTO) | ✅ |
| 4 | 서비스·CRUD·단위 테스트 | ✅ |
| 5 | API 라우터 계층 | 🔄 진행 예정 |
| 6 | Dify 연동·통합 테스트 | ⏳ |
| 7 | ARQ 백그라운드 잡·배포 | ⏳ |

세부 WBS는 [`docs/plans/plan.md`](docs/plans/plan.md) 참조.

---

## 기여·워크플로 규칙

이 프로젝트는 **문서 주도 개발(SDD)** 기반으로, 코딩 전 설계 승인(Gate A) → 구현 → 테스트 계획 승인(Gate C) → 검증 → 이력 이전(Gate E) 순서를 준수합니다.

- **게이트 워크플로**: [`docs/rules/workflow_gates.md`](docs/rules/workflow_gates.md)
- **백엔드 아키텍처 규칙**: [`docs/rules/backend_architecture.md`](docs/rules/backend_architecture.md)
- **Dify 연동 규칙**: [`docs/rules/dify_integration.md`](docs/rules/dify_integration.md)
- **아키텍처 설계서(SDD)**: [`ref_files/IDR_Data_Analysis_SDD.md`](ref_files/IDR_Data_Analysis_SDD.md)
- **커밋 메시지**: 한국어 Conventional Commits — `feat(범위): 한글 제목`
- **추적 제외·비밀**: **`.env`로 시작하는 파일 전부** (패턴 `.env*`)·키·Dify 볼륨 등은 **커밋하지 않음**. 템플릿은 `env.example`·`env.prod.example`·`infra/dify/env.vendor.example` 사용. 상세는 [`docs/rules/project_context.md`](docs/rules/project_context.md) **「Git · 추적 제외 및 비밀 관리」** 절.

### Git 커밋 전 체크리스트

```bash
make format && make lint && make typecheck   # 품질 게이트 통과
git add -A                                   # 변경분 전부 스테이징 (stash 충돌 방지)
git commit                                   # pre-commit 훅 자동 실행
```

---

<div align="center">

**IDR Systems** · `idr_analytics` v0.1.0  
Python 3.12+ · FastAPI · Pandas · Prophet · scikit-learn · Dify

</div>
