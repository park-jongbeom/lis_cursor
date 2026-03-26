# 프로젝트 컨텍스트 — IDR 시스템 데이터 분석 AI 백엔드

> 이 파일을 읽는 AI에게: 코드를 작성하기 전에 이 문서 전체를 읽어라.
> 세부 아키텍처 결정 근거는 `ref_files/IDR_Data_Analysis_SDD.md` (v1.1.0)에 있다.

---

## 프로젝트 정체성

| 항목 | 내용 |
|------|------|
| **서비스명** | IDR 시스템 데이터 분석 AI 에이전트 백엔드 (`idr_analytics`) |
| **목적** | IDR 시스템즈의 LIS(유전자 검사 의뢰 관리) 데이터를 AI로 분석하여 비즈니스 의사결정 자동화 |
| **고객사** | IDR 시스템즈 — 유전자 검사 의뢰, 수가, 청구수금, 매출 등 정형 데이터 보유 |
| **기반 아키텍처** | `labeling_vscode_claude` 프로젝트의 2-Tier 하이브리드 라우팅 패턴을 정형 데이터(CSV)에 재적용 |
| **개발 방법론** | 문서 주도 개발(SDD) — 스펙 확정 후 구현 |
| **컨텍스트 전달 대상** | Cursor AI (이 `.cursorrules` 체계) |

---

## 3가지 비즈니스 목표 (절대 잊지 마라)

| # | 도메인 | 목표 | AI 기법 | 엔드포인트 접두사 |
|---|--------|------|---------|-------------------|
| BG-1 | **SCM** | 시약·키트 수요 예측 및 재고 최적화 | Prophet / ARIMA 시계열 예측 | `/api/v1/scm/` |
| BG-2 | **CRM** | 거래처 이탈 징후 감지 및 잠재 고객 클러스터링 | K-Means / RFM 분석 | `/api/v1/crm/` |
| BG-3 | **BI** | 지역·시기별 질환 트렌드 분석 | GroupBy Pivot + LLM 요약 | `/api/v1/bi/` |

---

## 기술 스택 (Spring Boot 비유 포함)

| 계층 | 기술 | 버전 | Spring Boot 비유 |
|------|------|------|------------------|
| API Framework | **FastAPI** | Python 3.12+ | Spring MVC + @RestController |
| 데이터 처리 | **Pandas 2.x**, NumPy | — | Stream API + DTO |
| 시계열 예측 | **Prophet** (Meta), statsmodels ARIMA | — | Spring Batch Job |
| 클러스터링 | **scikit-learn** (K-Means, DBSCAN) | — | MLflow Pipeline |
| AI 오케스트레이션 | **Self-hosted Dify** (Docker Compose 로컬 설치) | — | Camunda Workflow Engine |
| LLM 클라이언트 | **Claude API** (anthropic), Ollama (온프레미스 옵션) | — | OpenFeign HTTP Client |
| ORM | **SQLAlchemy 2.0** (Async) | — | JPA + Hibernate |
| 마이그레이션 | **Alembic** | — | Flyway |
| 비동기 워커 | **ARQ** (Redis-backed) | — | @Async + @EnableAsync |
| 캐시 | **Redis** | — | Spring Cache (@Cacheable) |
| DB | **PostgreSQL 15+** | — | PostgreSQL |
| HTTP 클라이언트 | **httpx** | ^0.27 | RestTemplate / WebClient |
| 컨테이너 | **podman-compose** (Docker Compose 호환) | — | Docker Compose |

---

## 프로젝트 디렉토리 구조

```
idr_analytics/
├── app/
│   ├── main.py                         # FastAPI app + lifespan
│   ├── api/v1/
│   │   ├── api.py                      # 라우터 통합
│   │   └── endpoints/
│   │       ├── auth.py
│   │       ├── datasets.py             # CSV 업로드·프로파일링
│   │       ├── scm.py                  # BG-1: 수요 예측
│   │       ├── crm.py                  # BG-2: 고객 클러스터링
│   │       ├── bi.py                   # BG-3: 트렌드 분석
│   │       └── agent.py                # Dify 프록시 (자연어 쿼리)
│   ├── core/
│   │   ├── config.py                   # Pydantic Settings
│   │   ├── dependencies.py             # FastAPI Depends
│   │   └── routing.py                  # ComplexityScorer
│   ├── db/
│   │   ├── session.py
│   │   └── base.py
│   ├── models/                         # SQLAlchemy ORM
│   ├── schemas/                        # Pydantic DTO
│   ├── services/
│   │   ├── data/
│   │   │   ├── ingestion_service.py    # CSV → validated DataFrame
│   │   │   └── preprocessing_service.py
│   │   ├── analytics/
│   │   │   ├── routing_service.py      # 하이브리드 라우터
│   │   │   ├── scm_service.py          # Prophet / ARIMA
│   │   │   ├── crm_service.py          # K-Means + RFM
│   │   │   └── bi_service.py           # GroupBy + Pivot
│   │   └── ai/
│   │       └── agent_service.py        # Dify Workflow API 프록시
│   ├── crud/
│   └── workers/
│       └── arq_worker.py
├── alembic/
├── tests/
│   ├── unit/
│   └── integration/
├── .env.example
├── pyproject.toml
├── docker-compose.yml                  # PostgreSQL + Redis (idr 전용)
└── docker-compose.dify.yml            # Self-hosted Dify 스택
```

---

## 실행 환경 (고정 사항 — 매 세션 재확인 금지)

| 항목 | 값 | 비고 |
|------|----|----|
| **OS** | RHEL 8 (kernel 4.18.0-553.56.1.el8_10) | 구형 커널 |
| **컨테이너 런타임** | rootless podman (Docker CLI 호환) | `docker` 명령 = podman 에뮬레이션 |
| **컨테이너 관리** | `podman-compose` | docker-compose 호환 |
| **SELinux** | Enabled | `podman build` 중 apt-get 단계에서 메모리 보호 충돌 |
| **Python (호스트)** | 3.13.2 (`/home/lukus/miniconda3/bin/python`) | 프로젝트 타겟은 3.12 |
| **pytest 실행** | 호스트 miniconda에서 `PYTHONPATH=idr_analytics poetry run pytest idr_analytics/tests/` | 컨테이너 빌드 불가로 호스트 직접 실행 |

> **컨테이너 빌드 실패 원인**: RHEL 8 + rootless podman + SELinux → glibc RELRO 메모리 보호 충돌.
> ruff, mypy, pre-commit, pytest는 호스트 miniconda에서 직접 실행한다. 이는 Docker First 원칙의 예외가 아닌, 개발 워크플로 도구이기 때문이다.

---

## 작업 프로토콜 (반드시 준수)

어떤 태스크를 받더라도 아래 Gate 순서를 지키고, **각 Gate 전환 전 개발자 승인**을 받는다. 절차 전문·금지 사항·`CURRENT` 표준 섹션은 **`docs/rules/workflow_gates.md`** 가 단일 원본이다. Cursor 에이전트용 요약은 **`.cursor/skills/idr-session-workflow/SKILL.md`** 를 참고한다. `docs/CURRENT_WORK_SESSION.md`의 워크플로 표와 동일하다.

| 단계 | Gate |
|------|------|
| `plan`/참조 확인 후 **구현 상세 계획** CURRENT 작성·사용자 승인 (코딩 전) | A |
| **구현** 후 구현 완료 요약·체크리스트·사용자 승인 | B |
| **테스트 상세 계획** CURRENT·사용자 승인 (테스트 실행 전) | C |
| 테스트 실행·검증 결과 기록 | D |
| `WORK_HISTORY`·`plan.md` 체크·다음 세션 CURRENT | E |

구현 시 관례: 소스에는 **클래스/함수 수준 Docstring만** (튜토리얼식 주석 금지). 설명은 Spring Boot / Kotlin / JPA / Flyway 비유를 사용한다. pytest 예시: `PYTHONPATH=idr_analytics poetry run pytest idr_analytics/tests/` (또는 `CURRENT`에 적힌 명령).
