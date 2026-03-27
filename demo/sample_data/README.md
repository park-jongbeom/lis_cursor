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
  - 품목당 24행(총 72행)·완만한 추세/변동 포함, `test_code` 3종 §3.1
- `crm_sample.csv`
  - 탭: CRM 이탈·클러스터
  - **필수** (`crm_service.CRM_REQUIRED`): `customer_code`, `order_date`, `order_amount`
  - **권장**: `customer_name` (표·차트 가독성) §3.2
  - 15고객 x 3주문(총 45행), 마지막 주문일 분산으로 이탈 위험군/활성군 동시 노출 §3.2
- `bi_sample.csv`
  - 탭: BI 트렌드
  - 기본 매핑: `period_col=period`, `region_col=region`, `value_col=value`, `year_col=year`
  - 5지역 x 2검사 x 9기간(총 90행), **`period=2024-01`** 포함 §3.3
- `lis_orders_sample.csv`
  - 용도: **실제 LIS 화면 컬럼형** 원본 샘플 (`ref_files/idr_screenshots/검사의뢰조회.png` 기반)
  - 주요 컬럼: `request_date`, `request_no`, `customer_code`, `customer_name`, `region`, `test_code`, `test_name`, `specimen_code`, `specimen_name`, `department_code`, `sales_amount`
  - 분석 전처리 예시(필드 매핑):
    - SCM: `request_date -> order_date`, `test_code -> test_code`, `sales_amount -> order_qty(또는 수량 대체지표)`
    - CRM: `customer_code/customer_name` 유지, `request_date -> order_date`, `sales_amount -> order_amount`
    - BI: `request_date -> period(YYYY-MM)`, `region -> region`, `test_code -> test_code`, `sales_amount -> value`

## 원본형 -> 데모형 자동 변환

`lis_orders_sample.csv`를 기준으로 데모용 CSV 3종을 자동 생성할 수 있습니다.

```bash
PYTHONPATH=idr_analytics poetry run python demo/sample_data/transform_lis_to_demo.py
```

생성 파일:

- `demo/sample_data/scm_from_lis.csv`
- `demo/sample_data/crm_from_lis.csv`
- `demo/sample_data/bi_from_lis.csv`
- `demo/sample_data/mixed_from_lis.csv`

SCM 변환 규칙:

- `test_code` 매출 합계 상위 4개 코드만 사용
- 주간(`W-SUN` 기반, 월요일 시작) 매출 합계로 `order_qty` 생성
- 코드별 누락 주차는 `0`으로 채워 예측 시계열 안정화

SCM 실행 팁( `scm_from_lis.csv` ):

- 데모 UI의 `test_codes` 입력에 `A002,A003,OS002,S003` 를 넣으면
  폴링 결과에서 예측 시리즈가 안정적으로 표시된다.

Mixed 데이터셋 팁( Dify CRM+BI 동시 실행 ):

- `mixed_from_lis.csv`는 CRM 필수(`customer_code`,`order_date`,`order_amount`)와
  BI 필수(`period`,`region`,`value`,`test_code`)를 동시에 포함한다.
- Dify 워크플로에서 `dataset_id` 하나로 CRM+BI 노드를 동시에 호출하려면 이 파일 업로드를 권장한다.

## 빠른 시연 순서

1. `demo/index.html` 열기
2. 탭에 맞는 CSV 선택 → **dataset_type 일치** → 업로드
3. 생성된 `dataset_id` 확인
4. 탭별 버튼 실행
   - SCM: `예측 실행 → 폴링`
   - CRM: `이탈 위험 분석`, `클러스터 실행 → 폴링`
   - BI: `지역 히트맵`, `YoY 비교`

하나의 CSV로 세 탭을 동시에 쓰지 말 것(§1 비목표). 탭별 전용 파일 권장.
