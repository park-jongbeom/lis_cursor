# `demo/sample_data/` 샘플 CSV — 동작 검증 상세 테스트 계획

> **목적**: 저장소에 포함된 **`scm_sample.csv` · `crm_sample.csv` · `bi_sample.csv`** 로 실제 플로우(업로드 → DB 메타 저장 → 분석 API)가 **정상 종료**하는지 증명한다.  
> **자동 회귀**: `make test` 통합 단계에서 **`idr_analytics/tests/integration/test_api_sample_data_upload.py`** 가 테스트 DB(`15433`)에 동일 CSV 3종을 업로드하고 프로필·핵심 분석 GET까지 검증한다.  
> **여전히 필요한 수동 증명**: 브라우저 데모 UI(`demo/index.html`)·Dify HTTP 노드·ARQ **forecast/cluster 폴링** 등은 pytest로 대체되지 않으므로, 아래 트랙 A/B·체크리스트를 따른다 (`DEMO_SAMPLES_PLAN.md` §5).

---

## 1. 검증 대상 파일·기대 행 수

| 파일 | `dataset_type` (업로드 시) | 데이터 행 수(헤더 제외) | 필수·기본 컬럼 |
|------|---------------------------|------------------------|----------------|
| `scm_sample.csv` | `scm` | **30** | `order_date`, `test_code`, `order_qty` |
| `crm_sample.csv` | `crm` | **24** | `customer_code`, `order_date`, `order_amount` + 권장 `customer_name` |
| `bi_sample.csv` | `bi` | **36** | `period`, `year`, `region`, `test_code`, `value` |

업로드 성공 시 API 응답(`DatasetProfileResponse`)의 **`row_count`** 가 위와 **일치**해야 한다.

---

## 2. 환경 선택 (둘 중 하나)

### 트랙 A — 개발 DB (브라우저 데모와 동일, 권장)

| 항목 | 값 |
|------|-----|
| Postgres | `localhost:15432`, DB `idr_analytics` (`.env`의 `DATABASE_URL`) |
| Redis | `localhost:6379` |
| 앱 | `make dev-up` → `make migrate` → `PYTHONPATH=idr_analytics poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| UI | `demo/index.html` + `demo/README.md` (CORS·`admin`·토큰) |

### 트랙 B — 테스트 DB (격리 검증)

| 항목 | 값 |
|------|-----|
| Postgres | `localhost:15433`, DB `idr_test` |
| Redis | `localhost:6380` (ARQ 워커를 실제로 띄울 때 동일 URL 필요) |
| 앱 기동 | `test-infra-up` → `migrate-test` 후, **일회성으로** `DATABASE_URL`·`REDIS_URL`·`SECRET_KEY` 등을 `migrate-test`와 동일하게 맞춘 뒤 uvicorn 실행 |

**주의**: 트랙 B에서 검증 후 `test-infra-down` 하면 **볼륨 삭제로 업로드 데이터도 사라진다**. 증빙이 필요하면 검증 중 `pg_dump` 또는 스크린샷·로그를 남긴다.

---

## 3. 공통 전제 조건

1. **사용자 1명**: DB에 `users` 행 존재(예: `admin`). 없으면 `demo/README.md` 시드 스니펫.
2. **인증**: `POST /api/v1/auth/login` → `access_token` 또는 개발용 `INTERNAL_BYPASS_*` + 동일 Bearer.
3. **헬스**: `GET http://127.0.0.1:8000/health` — 200 (`app.main` 기준, `/api/v1` 접두 없음).
4. **ARQ**: SCM 예측·CRM 클러스터 **완료까지** 보려면 `demo/README.md` 의 ARQ 워커 명령으로 **Redis와 동일 `REDIS_URL`** 에 연결. 워커 없이도 **업로드·동기 GET API(이탈·히트맵·YoY)** 는 검증 가능.

---

## 4. 테스트 케이스 (샘플별)

### TC-SCM-01 — `scm_sample.csv` 업로드·DB 메타

| 단계 | 행위 | 기대 |
|------|------|------|
| 1 | `multipart/form-data`: `file`=본 CSV, `dataset_name`=임의, `dataset_type`=`scm` | HTTP **201**, 본문에 `dataset_id`, `row_count`==**30**, `columns`에 `order_date`,`test_code`,`order_qty` |
| 2 | `GET /api/v1/datasets/{dataset_id}/profile` (Bearer) | **200**, `row_count`==30, dtype·null_counts 존재 |
| 3 | (선택) DB 직접 | `analysis_datasets`에서 해당 `id`의 `row_count=30`, `file_path` 파일이 디스크에 존재 |

### TC-SCM-02 — SCM 예측 잡 (샘플 `dataset_id` 사용)

| 단계 | 행위 | 기대 |
|------|------|------|
| 1 | `POST /api/v1/scm/forecast` body: `dataset_id`, `target_column`=`order_qty`, `date_column`=`order_date`, `group_by`=`test_code`, `forecast_days`=30, `test_codes`=[], `model`=`prophet` | **202**, `job_id` |
| 2 | 워커 기동 시 `GET .../scm/forecast/{job_id}` 폴링 | `status`=`completed`, `result.forecasts` 비어 있지 않음 |
| 2′ | 워커 미기동 | `pending`/`running`에서 정지 가능 → **TC-SCM-01만으로 샘플 적재는 검증됨** |

### TC-CRM-01 — `crm_sample.csv` 업로드·DB 메타

| 단계 | 행위 | 기대 |
|------|------|------|
| 1 | 업로드 `dataset_type`=`crm` | **201**, `row_count`==**24** |
| 2 | `GET .../profile` | 컬럼에 `customer_code`,`order_date`,`order_amount` (및 `customer_name`) |

### TC-CRM-02 — 이탈 위험 (동기, 워커 불필요)

| 단계 | 행위 | 기대 |
|------|------|------|
| 1 | `GET /api/v1/crm/churn-risk?dataset_id=...&compact=false` | **200**, `high_risk_customers` 배열(또는 빈 배열은 데이터·기준일에 따라 허용), **5xx 없음** |

### TC-CRM-03 — 클러스터 잡

| 단계 | 행위 | 기대 |
|------|------|------|
| 1 | `POST /api/v1/crm/cluster` `n_clusters`=4 | **202**, `job_id` |
| 2 | 워커 기동 시 폴링 | `completed`, 샘플·세그먼트 필드 존재 |

### TC-BI-01 — `bi_sample.csv` 업로드·DB 메타

| 단계 | 행위 | 기대 |
|------|------|------|
| 1 | 업로드 `dataset_type`=`bi` | **201**, `row_count`==**36** |

### TC-BI-02 — 지역 히트맵 (`period` 정합)

| 단계 | 행위 | 기대 |
|------|------|------|
| 1 | `GET /api/v1/bi/regional-heatmap?dataset_id=...&period=2024-01&compact=false` (+ 기본 컬럼명 쿼리) | **200**, `heatmap` 길이 ≥1, **404** `No rows for period` 아님 |

### TC-BI-03 — YoY

| 단계 | 행위 | 기대 |
|------|------|------|
| 1 | `GET /api/v1/bi/yoy-comparison?dataset_id=...&year_col=year&value_col=value&compact=false` | **200**, `yoy_by_year`에 2023·2024 등 키 존재 |

---

## 5. DB 직접 확인 예시 (선택·PostgreSQL)

트랙 A 기준 (`idr_analytics`):

```sql
SELECT id, name, dataset_type, row_count, file_path, created_at
FROM analysis_datasets
ORDER BY created_at DESC
LIMIT 5;
```

`columns_json` 확인:

```sql
SELECT id, row_count, columns_json->'columns' AS cols
FROM analysis_datasets
WHERE id = '<업로드 응답의 uuid>';
```

---

## 6. curl 업로드 예시 (UI 없이 트랙 A/B 공통)

```bash
TOKEN='<JWT>'
CSV=demo/sample_data/scm_sample.csv
curl -sS -X POST "http://127.0.0.1:8000/api/v1/datasets/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$CSV" \
  -F "dataset_name=tc_scm_sample" \
  -F "dataset_type=scm"
```

`crm`·`bi`는 `dataset_type`·파일 경로만 바꾼다.

---

## 7. 성공·실패 판정

| 구분 | 성공 최소선 (샘플 데이터 검증 목적) |
|------|-------------------------------------|
| **필수** | 세 파일 각각 **업로드 201** + **row_count 정합** + **TC-CRM-02** + **TC-BI-02**·**TC-BI-03** 200 |
| **권장** | SCM·CRM **ARQ** 경로까지 `completed` (워커 기동 환경) |
| **선택** | Dify 워크플로에서 동일 `dataset_id`·`period=2024-01` 호출 |

실패 시 `400`(CSV 파싱)·`401`·`403`·`404`(period 불일치)·`5xx` 원인을 로그·응답 `detail`에 기록한다.

---

## 8. Gate D 기록 템플릿

- 일시·트랙(A/B)·커밋 해시(선택)
- TC-SCM-01 ~ TC-BI-03 각 통과/스킵(ARQ)·실패 사유
- (선택) `analysis_datasets` 마지막 N건 스크린샷·쿼리 결과

---

## 9. 관련 문서

- 스펙·§8 대조표: [`DEMO_SAMPLES_PLAN.md`](DEMO_SAMPLES_PLAN.md)
- 데모 UI·인프라: [`../README.md`](../README.md)
- 세션 Gate 연동: `docs/CURRENT_WORK_SESSION.md` — 샘플 검증 시 **본 문서를 Gate C 보조 계획**으로 인용 가능
