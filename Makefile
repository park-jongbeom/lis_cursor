# IDR Analytics — 개발·테스트·배포 편의 명령
# 실행 환경: RHEL 8, rootless podman-compose

COMPOSE_TEST = podman-compose -f docker-compose.test.yml
COMPOSE_DEV  = podman-compose -f docker-compose.dev.yml
COMPOSE_PROD = podman-compose -f docker-compose.prod.yml
# Dify 1.13+ : 공식 compose + IDR 오버레이 (항상 vendor/ 에서 실행)
DIFY_VENDOR_DIR := infra/dify/vendor
define DIFY_COMPOSE_CMD
mkdir -p "$$HOME/tmp" && cd $(DIFY_VENDOR_DIR) && TMPDIR="$$HOME/tmp" podman-compose --profile weaviate --profile postgresql -f docker-compose.yaml -f ../docker-compose.idr.yml --env-file ../.env
endef
ALEMBIC      = PYTHONPATH=idr_analytics poetry run alembic -c idr_analytics/alembic/alembic.ini
PYTEST       = PYTHONPATH=idr_analytics poetry run pytest

# 공개 데모(역프록시 끝점) — `make open-lis` 로 기본 브라우저 실행
LIS_DEMO_URL ?= https://lis.qk54r71z.freeddns.org/

# ── 테스트 인프라 ──────────────────────────────────────────────────────────────

.PHONY: test-infra-up
test-infra-up:
	$(COMPOSE_TEST) up -d
	@echo "Waiting for postgres-test to be healthy..."
	@until podman healthcheck run idr-postgres-test 2>/dev/null; do sleep 2; done
	@echo "idr-postgres-test is healthy."

.PHONY: test-infra-down
## podman-compose down 은 dev pod(pod_lis_cursor)와 충돌해 Error 로그가 남을 수 있어, 테스트 전용 리소스만 명시 제거
test-infra-down:
	podman rm -f idr-postgres-test idr-redis-test 2>/dev/null || true
	podman network rm idr-test_idr-test-net 2>/dev/null || true
	podman volume rm idr-test_pgdata-test 2>/dev/null || true

.PHONY: test-infra-clean-legacy
## Session 11 이전(compose 프로젝트명이 디렉터리 기본값이던 시기)에 남은 테스트 볼륨·네트워크만 제거 시도 — idr-test 도입 후에는 보통 불필요
test-infra-clean-legacy:
	podman volume rm lis_cursor_pgdata-test 2>/dev/null || true
	podman network rm lis_cursor_idr-test-net 2>/dev/null || true

# ── 마이그레이션 ───────────────────────────────────────────────────────────────

.PHONY: migrate
migrate:
	$(ALEMBIC) upgrade head

.PHONY: migrate-test
# 테스트 DB 마이그레이션 — 비밀값은 .env.test 또는 환경 변수에서 읽음
# .env.test 예시: POSTGRES_PASSWORD=idr-test-pw (gitignore 처리됨)
migrate-test:
	DATABASE_URL=postgresql+asyncpg://idr:$${POSTGRES_PASSWORD:-idr-test-pw}@localhost:15433/idr_test \
	REDIS_URL=redis://localhost:6380/1 \
	SECRET_KEY=$${SECRET_KEY:-test-secret-key-32chars-minimum!!} \
	ANTHROPIC_API_KEY=sk-ant-test \
	DIFY_API_KEY=app-test \
	DIFY_WORKFLOW_ID=test-workflow \
	$(ALEMBIC) upgrade head

# ── 테스트 실행 ────────────────────────────────────────────────────────────────

.PHONY: test-unit
test-unit:
	$(PYTEST) idr_analytics/tests/unit/ -v

.PHONY: test-unit-cov
test-unit-cov:
	$(PYTEST) idr_analytics/tests/unit/ --cov=app --cov-report=term-missing -v

.PHONY: test-integration
test-integration:
	$(PYTEST) idr_analytics/tests/integration/ -v

.PHONY: test
## 전체 테스트: 테스트 인프라 기동 → 마이그레이션 → 단위+통합 → 인프라 종료
test: test-infra-up migrate-test test-unit test-integration test-infra-down

# ── 개발 인프라 ────────────────────────────────────────────────────────────────

.PHONY: dev-up
dev-up:
	$(COMPOSE_DEV) up -d

.PHONY: dev-down
dev-down:
	$(COMPOSE_DEV) down

# ── 로컬 «운영형» 인프라 (테스트·dev 과 동시 기동 금지 — 컨테이너 이름 충돌) ───────

.PHONY: prod-up
prod-up:
	@test -f .env.prod || (echo "오류: .env.prod 없음 — cp env.prod.example .env.prod 후 편집"; exit 1)
	$(COMPOSE_PROD) --env-file .env.prod up -d

.PHONY: prod-down
prod-down:
	$(COMPOSE_PROD) down

.PHONY: migrate-prod
## `.env.prod` 를 로드한 뒤 운영형 로컬 DB 에 Alembic 적용
migrate-prod:
	@test -f .env.prod || (echo "오류: .env.prod 없음"; exit 1)
	bash -lc 'set -a && source ./.env.prod && set +a && $(ALEMBIC) upgrade head'

.PHONY: open-lis
## 기본 브라우저에서 `LIS_DEMO_URL` 열기 (Linux: xdg-open)
open-lis:
	@echo "Opening $(LIS_DEMO_URL)"
	@command -v xdg-open >/dev/null 2>&1 && exec xdg-open "$(LIS_DEMO_URL)" || \
		command -v gio >/dev/null 2>&1 && exec gio open "$(LIS_DEMO_URL)" || \
		(echo "xdg-open 또는 gio 가 없습니다. 수동으로 열기: $(LIS_DEMO_URL)"; exit 1)

# ── Dify 인프라 ────────────────────────────────────────────────────────────────

.PHONY: dify-env-bootstrap
## Dify용 infra/dify/.env 생성 (env.vendor.example 복사 — vendor/.env.example 은 Git 무시)
dify-env-bootstrap:
	@test -f infra/dify/.env && echo "infra/dify/.env 이미 있음" || cp infra/dify/env.vendor.example infra/dify/.env
	@echo "다음: infra/dify/.env 에서 EXPOSE_NGINX_PORT=8080, SECRET_KEY, DB_PASSWORD, REDIS_PASSWORD 확인"

.PHONY: dify-up
## Dify Self-hosted 스택 기동 (공식 1.13.x + infra/dify/docker-compose.idr.yml)
## 1) infra/dify/.env 존재 확인 (없으면: make dify-env-bootstrap 또는 cp infra/dify/env.vendor.example)
## 2) idr-net 생성
## 3) vendor/ 에서 compose 기동 — Web UI: http://localhost:8080
dify-up:
	@test -f infra/dify/.env || (echo "오류: infra/dify/.env 없음. 실행: make dify-env-bootstrap"; echo "      편집: EXPOSE_NGINX_PORT=8080, SECRET_KEY/DB_PASSWORD/REDIS_PASSWORD 변경"; exit 1)
	@podman network exists idr-net 2>/dev/null || podman network create idr-net
	@$(DIFY_COMPOSE_CMD) up -d
	@echo "Dify 1.13 스택 기동. Web UI: http://localhost:8080 (EXPOSE_NGINX_PORT 기준)"
	@echo "설정: infra/dify/README.md | 공개 URL은 infra/dify/.env 의 CONSOLE_API_URL / APP_API_URL"
	@echo "Tip: make dify-logs-api"

.PHONY: dify-down
## Dify Self-hosted 스택 종료 (볼륨 유지)
dify-down:
	@$(DIFY_COMPOSE_CMD) down

.PHONY: dify-down-v
## Dify 스택 종료 + compose 기본 볼륨 삭제 (바인드 마운트 vendor/volumes/ 는 수동 rm 가능)
dify-down-v:
	@$(DIFY_COMPOSE_CMD) down -v

.PHONY: dify-logs
## Dify 전 서비스 로그 (vendor 디렉터리 기준)
dify-logs:
	@$(DIFY_COMPOSE_CMD) logs --tail=50 -f

.PHONY: dify-logs-api
## Dify API 컨테이너 로그만
dify-logs-api:
	@$(DIFY_COMPOSE_CMD) logs --tail=80 -f api

.PHONY: dify-ps
## Dify 컨테이너 상태 확인
dify-ps:
	@$(DIFY_COMPOSE_CMD) ps

.PHONY: dify-fastapi-jwt
## FastAPI 로그인 JWT 출력 — 환경 변수 IDR_API_BASE_URL(선택), IDR_LOGIN_USERNAME, IDR_LOGIN_PASSWORD 필요. Dify용 헤더: make dify-fastapi-jwt-bearer
dify-fastapi-jwt:
	@poetry run python infra/dify/scripts/fetch_fastapi_jwt.py

.PHONY: dify-fastapi-jwt-bearer
## 위와 동일 + `Authorization: Bearer <token>` 한 줄 출력
dify-fastapi-jwt-bearer:
	@poetry run python infra/dify/scripts/fetch_fastapi_jwt.py --bearer

.PHONY: ollama-dify-host-bind
## 호스트 Ollama를 0.0.0.0:11434에 바인딩 (systemd drop-in, sudo 필요) — Dify 모델 공급자 검증용
ollama-dify-host-bind:
	@bash infra/ollama/apply-dify-host-bind.sh

# ── 코드 품질 ──────────────────────────────────────────────────────────────────

.PHONY: format
format:
	PYTHONPATH=idr_analytics poetry run ruff format idr_analytics/

.PHONY: lint
lint:
	PYTHONPATH=idr_analytics poetry run ruff check idr_analytics/

.PHONY: lint-fix
lint-fix:
	PYTHONPATH=idr_analytics poetry run ruff check idr_analytics/ --fix

.PHONY: typecheck
typecheck:
	PYTHONPATH=idr_analytics poetry run mypy idr_analytics/app --strict

.PHONY: check
check: lint typecheck test-unit
