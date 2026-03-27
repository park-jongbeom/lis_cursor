# SCM `InterfaceError(connection is closed)` 검증 계획

## 1) 목표

- SCM 샘플 업로드 후 `예측 실행 -> 폴링` 경로에서 발생한
  `sqlalchemy.dialects.postgresql.asyncpg.InterfaceError: connection is closed`
  오류의 재현 가능성을 줄였는지 검증한다.
- 검증 범위를 "코드 설정", "API 스모크", "브라우저 E2E"로 분리해 누락을 방지한다.

## 2) 원인 가설

- PostgreSQL 연결이 유휴/재시작 등으로 끊긴 뒤, SQLAlchemy 풀에서 stale 연결을 재사용하면서
  `asyncpg InterfaceError(connection is closed)`가 발생했을 가능성이 높다.

## 3) 적용된 완화 조치

- 파일: `idr_analytics/app/db/session.py`
- 조치:
  - `pool_pre_ping=True` 추가 (체크아웃 시 끊긴 연결 감지 후 재연결)
  - `pool_recycle=1800` 추가 (장시간 유지 연결 재사용 최소화)

## 4) 검증 시나리오

### A. 단위 회귀 (완료)

- 목적: 엔진 설정이 회귀되지 않도록 고정
- 파일: `idr_analytics/tests/unit/test_db_session.py`
- 케이스:
  - pool pre-ping 활성화 확인
  - recycle 시간 1800초 확인

### B. API 스모크 (인프라 전제)

- 전제:
  - 개발 인프라 기동: `make dev-up`
  - 마이그레이션: `make migrate`
  - 필요 시 ARQ 워커 기동(`demo/README.md` 절차)
- 절차:
  1. `/health` 200 확인
  2. SCM CSV 업로드 후 `dataset_id` 획득
  3. `POST /api/v1/scm/forecast` 호출 -> `job_id` 확인
  4. `GET /api/v1/scm/forecast/{job_id}` 반복 폴링
  5. 실패 시 서버 로그에서 `InterfaceError` 발생 유무 확인

### C. 브라우저 E2E (사용자 실행)

- 사이트: `https://lis.qk54r71z.freeddns.org/`
- 절차:
  1. 인증(Bearer/JWT) 설정
  2. SCM 샘플 업로드
  3. 예측 실행 -> 폴링
  4. 실패 시 발생 시점/입력값/오류 원문 수집

## 5) 성공 기준

- 단위 회귀 통과
- API 폴링 구간에서 동일 `InterfaceError(connection is closed)` 미발생
- 브라우저 E2E에서 SCM 경로 1회 이상 정상 완료

## 6) 장애 재발 시 추가 조치

- DB 재시작/네트워크 단절 직후 재현 여부 분리 확인
- 필요 시 DB 작업 경계에서 1회 재시도(연결 예외 한정) 전략을 별도 설계
- 인프라 healthcheck/idle timeout 설정(Postgres, 프록시) 점검
