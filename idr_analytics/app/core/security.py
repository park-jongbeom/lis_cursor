"""비밀번호 검증 및 JWT 발급.

bcrypt 4.x와 passlib 1.7.4 조합에서 발생하는 백엔드 초기화 오류를 피하기 위해
해시 검증은 `bcrypt` 네이티브 API만 사용한다 ($2b$… 포맷 호환).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt

from app.core.config import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(plain: str) -> str:
    """신규 사용자·시드용 bcrypt 해시 (UTF-8)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: uuid.UUID,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": str(subject), "exp": expire}
    # jose 스텁이 str 이든 Any 든 str() 로 반환 타입을 str 로 통일 (pre-commit·로컬 mypy 공통)
    return str(jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256"))
