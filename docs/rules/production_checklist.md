# 운영 환경 점검 체크리스트 (`APP_ENV=production`)

`IDR Analytics` FastAPI·Postgres·Redis·(선택) Dify를 프로덕션에 올리기 전에 확인한다. 상세 변수 설명은 루트 `env.example`과 [`project_context.md`](project_context.md)를 참고한다.

## 1. 환경 변수

- [ ] `APP_ENV=production` (또는 운영에서 의도한 값)으로 설정되어 있다.
- [ ] `SECRET_KEY`가 개발용 기본값이 아니며, 충분한 길이·난수성을 갖는다.
- [ ] `ALLOWED_ORIGINS`가 JSON 배열 문자열 형식이며, 실제 프론트·게이트웨이 출처만 포함한다. (쉘에 남은 `export ALLOWED_ORIGINS`가 `.env`를 덮어쓰지 않았는지 확인.)
- [ ] `DATABASE_URL`이 `postgresql+asyncpg://`이며, 컨테이너 네트워크에서는 DB 호스트명·포트가 운영 구성과 일치한다.
- [ ] `REDIS_URL`이 운영 Redis에 연결된다 (ARQ 워커·캐시 등).
- [ ] Tier 2를 쓰는 경우 `DIFY_API_BASE_URL`, `DIFY_API_KEY`, `DIFY_WORKFLOW_ID`가 유효하다. Tier 1만 쓰면 키는 비워 둘 수 있으나 의도를 문서화한다.
- [ ] `INTERNAL_BYPASS_ENABLED=false` 이다 (운영에서 공유 Bearer 우회는 사용하지 않는다).

## 2. 인프라·스키마

- [ ] Postgres·Redis 컨테이너(또는 관리형 인스턴스)가 기동되었고 healthcheck가 통과한다.
- [ ] Alembic을 운영 DB에 대해 `upgrade head`까지 적용했다 (`0003_timestamptz` 등 최신 리비전 포함).
- [ ] `DATA_UPLOAD_DIR`(기본 `./data/uploads`)가 쓰기 가능한 볼륨으로 마운트되어 있다.

## 3. 보안

- [ ] `.env`·`.env.prod` 등 비밀 파일이 이미지·Git에 포함되지 않았다 (`git check-ignore` 등).
- [ ] 운영 DB·Redis에 강한 비밀번호와 네트워크 격리(방화벽·사설망)가 적용되어 있다.

## 4. 애플리케이션 기동 (`docker-compose.prod.yml`)

- [ ] **로컬에서 `APP_ENV=production`을 검증할 때**도 동일한다. `docker-compose.prod.yml`은 **로컬 «운영형» Postgres/Redis**용이며(`make prod-up`), 원격 전용이 아니다. 절차는 `infra/deploy/local-prod/README.md` 참고.
- [ ] `idr-postgres`, `idr-redis` 서비스 정의와 `.env.prod` 연동을 확인했다.
- [ ] `idr-fastapi` 블록은 **컨테이너 이미지 빌드·레지스트리 푸시·태그 확정 후** 주석을 해제한다. 해제 전에는 DB·Redis만 기동하는 구성일 수 있다.
- [ ] FastAPI를 붙일 때 `depends_on`에 healthy 조건이 맞고, 같은 `idr-net`에 속한다.

## 5. 배포 전 품질

- [ ] 로컬 또는 CI에서 `make format`, `make lint`, `make typecheck`가 통과했다.
- [ ] (권장) `make test`로 단위·통합 회귀를 통과했다. — **Gate C 승인 후** 저장소 관례에 따라 실행한다.

## 6. 배포 후 스모크

- [ ] `GET /health`(또는 운영에서 노출한 헬스 경로)가 성공한다.
- [ ] 로그 레벨·로그 드라이브가 운영 정책에 맞다 (uvicorn/FastAPI).

## 관련 파일

| 항목 | 경로 |
|------|------|
| 변수 템플릿 | 루트 `env.example` |
| 운영 Compose 초안 | `docker-compose.prod.yml` |
| Alembic | `idr_analytics/alembic/` |
