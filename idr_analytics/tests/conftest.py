"""pytest 공통 설정 — env var는 반드시 app.* import 전에 주입해야 한다.

app/db/session.py와 app/core/config.py가 모듈 레벨에서 settings를 즉시 참조하므로
pytest collection 단계에서 환경변수가 없으면 pydantic ValidationError가 발생한다.
autouse fixture는 collection 이후 실행되므로 이 파일 최상단에서만 처리한다.
"""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://idr:password@localhost:15433/idr_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-minimum!!")
os.environ.setdefault("AI_ESCALATION_THRESHOLD", "70")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("DIFY_API_KEY", "app-test")
os.environ.setdefault("DIFY_WORKFLOW_ID", "test-workflow")
