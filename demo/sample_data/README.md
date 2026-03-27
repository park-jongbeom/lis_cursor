# 데모용 샘플 CSV

`DEMO_SAMPLES_PLAN.md` §3 스펙에 맞춘 예제 데이터입니다. 검증 체크리스트·리스크는 동일 문서 §5·§6 참조.

**업로드→DB→분석 API**까지의 상세 테스트 계획(TC·기대 `row_count`·curl·SQL): [`SAMPLE_DATA_TEST_PLAN.md`](SAMPLE_DATA_TEST_PLAN.md)

## 시연 전제 (`DEMO_SAMPLES_PLAN.md` §2.3와 동일 계열)

1. JWT 또는 `INTERNAL_BYPASS_*` — `demo/README.md`
2. **탭별로 해당 CSV만** 업로드하고, `dataset_type`을 **`scm` / `crm` / `bi`** 중 시연 탭과 맞출 것
3. SCM·CRM **ARQ 잡**(예측·클러스터) 시연 시 **워커 기동** — `demo/README.md`

## 파일

- `scm_sample.csv`
  - 탭: SCM 수요예측
  - 기본 매핑: `target_column=order_qty`, `date_column=order_date`, `group_by=test_code`
  - 품목당 10행·그룹당 &lt;60행(ARIMA 경로), `test_code` 3종 §3.1
- `crm_sample.csv`
  - 탭: CRM 이탈·클러스터
  - **필수** (`crm_service.CRM_REQUIRED`): `customer_code`, `order_date`, `order_amount`
  - **권장**: `customer_name` (표·차트 가독성) §3.2
  - 고객 수 ≥4, 마지막 주문이 임계(기본 90일)보다 과거인 거래처 포함 §3.2
- `bi_sample.csv`
  - 탭: BI 트렌드
  - 기본 매핑: `period_col=period`, `region_col=region`, `value_col=value`, `year_col=year`
  - **`period` 문자열**은 `demo/index.html` 기본값 **`2024-01`** 과 동일한 행이 있음 §3.3

## 빠른 시연 순서

1. `demo/index.html` 열기
2. 탭에 맞는 CSV 선택 → **dataset_type 일치** → 업로드
3. 생성된 `dataset_id` 확인
4. 탭별 버튼 실행
   - SCM: `예측 실행 → 폴링`
   - CRM: `이탈 위험 분석`, `클러스터 실행 → 폴링`
   - BI: `지역 히트맵`, `YoY 비교`

하나의 CSV로 세 탭을 동시에 쓰지 말 것(§1 비목표). 탭별 전용 파일 권장.
