# IDR Analytics — 개발·테스트·배포 편의 명령
# 실행 환경: RHEL 8, rootless podman-compose

COMPOSE_TEST = podman-compose -f docker-compose.test.yml
COMPOSE_DEV  = podman-compose -f docker-compose.dev.yml
ALEMBIC      = PYTHONPATH=idr_analytics poetry run alembic -c idr_analytics/alembic/alembic.ini
PYTEST       = PYTHONPATH=idr_analytics poetry run pytest

# ── 테스트 인프라 ──────────────────────────────────────────────────────────────

.PHONY: test-infra-up
test-infra-up:
	$(COMPOSE_TEST) up -d
	@echo "Waiting for postgres-test to be healthy..."
	@until podman healthcheck run idr-postgres-test 2>/dev/null; do sleep 2; done
	@echo "idr-postgres-test is healthy."

.PHONY: test-infra-down
test-infra-down:
	$(COMPOSE_TEST) down -v

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
