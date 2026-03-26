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

## 3단계 작업 프로토콜 (반드시 준수)

어떤 태스크를 받더라도 아래 순서를 지키고, **각 단계 후 반드시 멈추고 개발자 승인을 기다린다.**  
문서 기준 게이트·표준 섹션은 **`docs/rules/workflow_gates.md`** 와 **`docs/CURRENT_WORK_SESSION.md`** 에 맞춘다.

### Step 1: 계획 문서화
- 코딩 전에 변경할 파일, 사용할 로직, 예상 사이드 이펙트를 먼저 설명한다.
- 완료 후: "계획 문서화가 완료되었습니다. 이 방향으로 코드 구현(Step 2)을 시작할까요?" 라고 묻고 대기.

### Step 2: 코드 구현
- 개발자 승인 후 구현한다.
- 소스코드 내에는 **클래스/함수 레벨 Docstring만** 작성 (튜토리얼식 주석 금지).
- 개발자 백그라운드(Spring Boot / Kotlin / JPA / Flyway)와 1:1 비유로 설명한다.
- **구현 종료 직후**: `docs/CURRENT_WORK_SESSION.md`에 **구현 완료 요약**을 작성하고, 진행 상태를 **사용자 확인 대기**로 표시한다. 체크리스트 `- [x]` 반영.
- **금지**: 사용자 검토 없이 `CURRENT_WORK_SESSION.md`를 다음 세션 과제만 담은 문서로 통째로 교체하는 것.
- 완료 후: "구현 내용을 `CURRENT_WORK_SESSION.md`에 기록했습니다. 검토해 주시면 테스트 계획(Step 3a)을 작성하겠습니다." 라고 하고 **대기**.

### Step 3a: 테스트 계획 (사용자 구현 확인 후)
- 사용자가 Step 2를 확인한 뒤에만, 동일 세션 문서의 **「테스트 계획」**에 범위·명령·우선순위를 적는다.
- 브리핑 후 승인 대기.

### Step 3b: 테스트 검증
- 승인 후 테스트 코드 작성 및 실행.
- 이 프로젝트 레이아웃: `PYTHONPATH=idr_analytics poetry run pytest idr_analytics/tests/` (또는 세션 문서에 적힌 명령).
- 결과를 **「테스트 검증 결과」**에 기록한다.
- 성공 및 사용자 최종 확인 후 `docs/history/WORK_HISTORY.md`에 이전하고, `CURRENT_WORK_SESSION.md`를 다음 과제 중심으로 갱신한다.
