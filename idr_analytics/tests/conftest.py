"""pytest 공통 설정 — env var는 반드시 app.* import 전에 주입해야 한다.

app/db/session.py와 app/core/config.py가 모듈 레벨에서 settings를 즉시 참조하므로
pytest collection 단계에서 환경변수가 없으면 pydantic ValidationError가 발생한다.
autouse fixture는 collection 이후 실행되므로 이 파일 최상단에서만 처리한다.

아래 값은 CI/단위 테스트 전용 더미(non-secret) 값이다.
실제 API 키는 여기에 절대 하드코딩하지 않는다.
실제 통합 테스트는 CI 환경 변수 또는 .env.test(gitignore)에서 주입한다.
"""

import os

# ── 테스트 전용 더미 값 (실제 비밀값 아님) ─────────────────────────────────────
_TEST_DB_URL = "postgresql+asyncpg://idr:idr-test-pw@localhost:15433/idr_test"
_TEST_SECRET = "test-secret-key-32chars-minimum!!"  # noqa: S105 — 테스트 픽스처
_TEST_ANTHROPIC_KEY = "sk-ant-test"  # noqa: S105 — 더미, 실제 API 호출 없음
_TEST_DIFY_KEY = "app-test"  # noqa: S105 — 더미

os.environ.setdefault("DATABASE_URL", _TEST_DB_URL)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SECRET_KEY", _TEST_SECRET)
os.environ.setdefault("AI_ESCALATION_THRESHOLD", "70")
os.environ.setdefault("ANTHROPIC_API_KEY", _TEST_ANTHROPIC_KEY)
os.environ.setdefault("DIFY_API_KEY", _TEST_DIFY_KEY)
os.environ.setdefault("DIFY_WORKFLOW_ID", "test-workflow")
