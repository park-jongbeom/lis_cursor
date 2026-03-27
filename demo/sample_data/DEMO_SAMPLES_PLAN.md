# 데모 샘플 CSV — 상세 계획 (Gate A 수준)

> **목적**: `demo/index.html`·FastAPI 분석 API·Dify HTTP 노드가 **동일한 컬럼 계약**으로 재현 가능한 최소 데모 데이터를 제공한다.  
> **참조 구현**: `idr_analytics/app/services/analytics/*.py`, `demo/index.html`, `demo/DEMO_SCRIPT.md`, `docs/rules/dify_integration.md` §HTTP 노드.

---

## 1. 목표·비목표

| 구분 | 내용 |
|------|------|
| **목표** | SCM(예측)·CRM(이탈/클러스터)·BI(히트맵/YoY) 각각 **업로드 1회 + 기본 입력값**으로 성공 경로 확인 |
| **목표** | Dify `regional-heatmap`의 **`period` 쿼리 문자열**이 CSV `period` 열 값과 **완전 일치**하도록 샘플 고정 |
| **비목표** | 실운영 LIS 스키마 전부 반영, 대용량·엣지케이스 스트레스 테스트 |
| **비목표** | 단일 CSV로 세 도메인 동시 커버(가능은 하나 유지보수·설명 비용 증가 — **탭별 전용 파일 권장**) |

---

## 2. 전제·공통 규칙

### 2.1 업로드·검증

- `POST /api/v1/datasets/upload`는 `ingestion_service.read_csv_validated`로 **pandas `read_csv`** 후 행 수만 확인한다.
- 업로드 시점에는 **도메인별 필수 컬럼 검증 없음** — 분석 API 호출 시 `KeyError`/`400` 가능.
- **따라서** 샘플은 “업로드 성공”뿐 아니라 **각 탭 버튼 1회**까지 통과하도록 컬럼·값을 설계한다.

### 2.2 포맷

- 인코딩: **UTF-8**
- 구분자: **쉼표(CSV)**
- 헤더: **첫 행 고정**, 컬럼명은 API/데모 HTML 기본값과 **문자열 동일**(대소문자·언더스코어 포함)

### 2.3 시연 동선 (권장)

1. 토큰: JWT 로그인 또는 개발용 `INTERNAL_BYPASS_*` ( `demo/README.md` )
2. **탭별로 해당 CSV만** 업로드 → `dataset_type`은 `scm` / `crm` / `bi` 중 탭과 맞출 것
3. SCM/CRM **ARQ 잡** 시연 시 워커 기동 필수 (`demo/README.md` §ARQ)

---

## 3. 도메인별 상세 스펙

### 3.1 SCM — `scm_sample.csv`

| 항목 | 내용 |
|------|------|
| **사용 탭** | SCM 수요예측 |
| **데모 기본 매핑** | `target_column=order_qty`, `date_column=order_date`, `group_by=test_code` |
| **필수 논리 컬럼** | `order_date`, `order_qty`, `test_code` (group 기준) |
| **행 수·시계열** | 품목(`test_code`)별로 **일별 또는 주 단위** 연속 구간. `SCMService`는 그룹당 행 `< 60`이면 **ARIMA(1,1,1)**, 이상이면 **Prophet** 시도 |
| **계획 행 수** | 품목당 **≥10행** (데모에서 곡선이 보이도록). 강의 안정성 위해 **동일 길이·동일 날짜 축** 권장 |
| **품목 수** | `test_code` **2~4개** — 차트 상위 5개 제한과 설명 시간 절충 |
| **값** | `order_qty`는 0 이상 정수 또는 실수; 추세가 약간 보이도록 단조 증가/노이즈 혼합 가능 |
| **검증(수동)** | 업로드 후 **예측 실행 → 폴링** 완료, `forecasts` 비어 있지 않음 |

### 3.2 CRM — `crm_sample.csv`

| 항목 | 내용 |
|------|------|
| **사용 탭** | CRM 이탈·클러스터 |
| **코드상 필수 컬럼** | `customer_code`, `order_date`, `order_amount` (`crm_service.CRM_REQUIRED`) |
| **이름** | `customer_name` — 없어도 동작하나 데모 표/차트 가독성 위해 **포함 권장** |
| **행 구조** | 고객당 **최소 1행 이상** 주문; RFM은 `groupby(customer_code).agg(last_order, frequency, monetary)` |
| **이탈 위험 노출** | `CHURN_RECENCY_THRESHOLD_DAYS`(기본 90) 초과인 고객이 `churn-risk` 응답에 나오도록, 일부 고객의 **마지막 주문일을 과거**로 배치 |
| **고객 수** | **≥ settings.KMEANS_DEFAULT_CLUSTERS(기본 4)** 명 — K-Means 의미 있음 |
| **검증(수동)** | `이탈 위험 분석` — `high_risk_customers` 또는 빈 목록(임계값 미만만 있으면 0건이 정상) + 404/500 없음. `클러스터 실행` — 잡 완료 및 샘플 행 |

### 3.3 BI — `bi_sample.csv`

| 항목 | 내용 |
|------|------|
| **사용 탭** | BI 트렌드 |
| **데모 기본 매핑** | `period_col=period`, `region_col=region`, `value_col=value`, `year_col=year`, 히트맵용 `test_code` (상위 검사 표시) |
| **필수 논리 컬럼** | `period`, `region`, `value`; YoY 탭 추가 시 `year` |
| **period 형식** | 문자열 일관성: 예 `YYYY-MM`. **데모 HTML 기본 `biPeriod` 값과 동일한 문자열**을 데이터에 포함 |
| **행 구조** | 동일 `period`에 **여러 region** × **여러 test_code** 가 있어야 히트맵·상위 검사가 풍부함 |
| **전기 대비 성장** | `regional_trend`는 지역별 정렬된 period에서 `growth_vs_prev` 계산 — **최소 2개 이상 period** (예 2023-10 … 2024-03) |
| **검증(수동)** | `지역 히트맵` — `404 No rows for period` 없이 표·차트. **입력 period ≠ CSV면 404** — 시연 전 문자열 복사 확인 |
| **Dify 연동** | 워크플로의 `period` 입력과 **동일 문자열** (`dify_integration.md` §3.2 노드 B) |

---

## 4. 산출물 목록 (이 계획의 완료 정의)

| 파일 | 역할 |
|------|------|
| `demo/sample_data/scm_sample.csv` | SCM 예측용 |
| `demo/sample_data/crm_sample.csv` | CRM 이탈/클러스터용 |
| `demo/sample_data/bi_sample.csv` | BI 히트맵/YoY용 |
| `demo/sample_data/README.md` | 빠른 사용법·기본 파라미터 |
| `demo/sample_data/DEMO_SAMPLES_PLAN.md` (본 문서) | 계획·검증 기준 |

(선택) 저장소 루트 `demo/README.md`에 샘플 디렉터리 링크 한 줄 — 중복 문서 최소화.

---

## 5. 검증 체크리스트 (Gate D에 해당하는 수동 항목)

**DB 환경**: 브라우저에서 `uvicorn` + 데모 UI로 검증할 때는 보통 **개발 스택** Postgres **`localhost:15432`** / DB `idr_analytics` (`.env`의 `DATABASE_URL`).  
**pytest `make test`** 는 **테스트 전용** **`localhost:15433`** / `idr_test` 를 쓰며 개발 DB와 데이터가 **공유되지 않는다**. 통합 테스트 **`idr_analytics/tests/integration/test_api_sample_data_upload.py`** 가 본 폴더 CSV 3종으로 업로드·프로필·일부 분석 API를 **자동 검증**한다. 브라우저·Dify·ARQ 폴링 등 **수동** 증명은 [`SAMPLE_DATA_TEST_PLAN.md`](SAMPLE_DATA_TEST_PLAN.md) · 아래 체크리스트를 따른다.

백엔드·Redis·DB·(필요 시) ARQ 워커 기준 (수동 스모크 요약):

- [ ] `scm_sample.csv` 업로드 → SCM **예측 폴링** 성공
- [ ] `crm_sample.csv` 업로드 → CRM **이탈 분석** 200, **클러스터** 잡 완료
- [ ] `bi_sample.csv` 업로드 → BI **히트맵** 200, `period` 미스매치 없음 → **YoY** 200
- [ ] (선택) Dify 앱에서 `dataset_id` + `period` 동일 값으로 CRM+BI HTTP 노드 연쇄 1회

---

## 6. 리스크·완화

| 리스크 | 완화 |
|--------|------|
| ARQ 미기동으로 SCM/CRM 잡 `pending` 고착 | 리허설 시 워커 프로세스 확인 (`demo/DEMO_SCRIPT.md`) |
| BI `period` 오타 | 샘플·HTML 기본값을 동일 문자열로 고정, 시연 전 복사 |
| Prophet 실패·환경 의존 | SCM 샘플은 그룹당 행 수를 **60 미만**으로 두면 ARIMA 경로로도 데모 가능(구현상 폴백) |

---

## 7. 변경 시 원칙

- 컬럼명 변경 시 **반드시** `demo/index.html` 기본값·`DEMO_SCRIPT.md`·Dify 노드 쿼리 문자열을 함께 검토
- 실데이터 기반 확장 시: CRM은 `CRM_REQUIRED` 유지, BI는 `period` 표기 체계(월/분기) 통일

---

## 8. 샘플 파일과 §3 스펙 대조 (구현 시 필수)

> 아래는 **저장소에 포함된 CSV**가 본 문서 §3을 만족하는지 점검한 결과다. 샘플을 고치면 이 표를 같이 갱신한다.

| § | 요구(요약) | `scm_sample.csv` | `crm_sample.csv` | `bi_sample.csv` |
|---|------------|:----------------:|:----------------:|:---------------:|
| 3.1 | 필수 컬럼 `order_date`,`order_qty`,`test_code` | ✅ | — | — |
| 3.1 | 품목당 ≥10행, 동일 날짜 축, 품목 2~4개 | ✅ 10행×3품목 | — | — |
| 3.1 | 그룹당 &lt;60행 → ARIMA 폴백 가능 | ✅ | — | — |
| 3.2 | 필수 `customer_code`,`order_date`,`order_amount` | — | ✅ | — |
| 3.2 | `customer_name` 권장 | — | ✅ | — |
| 3.2 | 고객 ≥4, 일부 마지막 주문 과거(이탈 노출) | — | ✅ 12고객 | — |
| 3.3 | `period`,`region`,`value`, YoY용 `year` | — | — | ✅ |
| 3.3 | `period`가 HTML 기본 `biPeriod`와 문자열 일치 | — | — | ✅ `2024-01` 등 |
| 3.3 | 동일 period에 다수 region×test_code | — | — | ✅ |
| 3.3 | period 구간 ≥2 (성장률 계산) | — | — | ✅ 2023-10~2024-03 |

---

## 9. 런타임 동작 검증 (업로드·DB)

스펙 대조(§8)와 별개로, 실제 API·DB 적재를 증명하려면 [`SAMPLE_DATA_TEST_PLAN.md`](SAMPLE_DATA_TEST_PLAN.md) 를 따른다.

---

*문서 버전: 샘플 파일과 동일 리비전에 맞춰 갱신할 것.*
