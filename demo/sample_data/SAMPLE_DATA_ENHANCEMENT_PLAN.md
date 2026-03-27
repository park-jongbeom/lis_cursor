# 샘플 데이터 보강 계획 (실행본)

## 목적

- 강의 데모에서 `SCM/CRM/BI` 버튼 실행 시 표·차트가 비거나 단조롭게 보이는 문제를 줄이고,
  `demo/index.html` 기본 입력값으로 바로 의미 있는 결과가 나오도록 샘플 밀도를 높인다.

## 입력 기준

- UI 기준: `demo/index.html`의 기본 컬럼 매핑과 파라미터
- 서비스 기준: `idr_analytics/app/services/analytics/*.py`의 필수 컬럼 계약
- 요청 기준: `ref_files/idr_screenshots` 참고(필요 시)

## 실행 전 점검

- `ref_files/idr_screenshots` 경로 확인 결과: 현재 파일 없음(0 files)
- 따라서 이번 보강은 UI/서비스 코드 계약을 단일 기준으로 수행

## 보강 계획

1. SCM: 품목별 시계열 길이를 확장(최소 20+ 포인트)하고 완만한 추세/변동 삽입
2. CRM: 고객 수와 주문 이력을 늘려 이탈 위험군/활성군이 함께 나오도록 분산
3. BI: 기간/지역/검사항목 축을 확장해 heatmap·YoY·top tests를 동시에 강화
4. 문서 동기화: `README`, `DEMO_SAMPLES_PLAN`의 행수/특성 업데이트

## 실행 결과

- `scm_sample.csv`: 72행 (3품목 x 24주)
- `crm_sample.csv`: 45행 (15고객 x 3주문)
- `bi_sample.csv`: 90행 (5지역 x 2검사 x 9기간)
- 문서 반영:
  - `demo/sample_data/README.md`
  - `demo/sample_data/DEMO_SAMPLES_PLAN.md`

## 후속 검증

- 자동: `idr_analytics/tests/integration/test_api_sample_data_upload.py` 회귀 실행
- 수동: `demo/index.html`에서
  - SCM: 예측 실행 -> 폴링
  - CRM: 이탈 위험 / 클러스터
  - BI: regional-heatmap(period=2024-01) / YoY
