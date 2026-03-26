"""FastAPI dependency injection (auth, DB)."""

from __future__ import annotations

import secrets
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Internal-only bypass: allow a shared bearer token in non-production environments.
    if (
        settings.APP_ENV.lower() == "development"
        and settings.INTERNAL_BYPASS_ENABLED
        and settings.INTERNAL_BYPASS_BEARER_TOKEN
        and secrets.compare_digest(token, settings.INTERNAL_BYPASS_BEARER_TOKEN)
    ):
        result = await db.execute(
            select(User).where(
                User.username == settings.INTERNAL_BYPASS_USERNAME,
                User.is_active == true(),
            )
        )
        bypass_user = result.scalar_one_or_none()
        if bypass_user is None:
            raise credentials_exc
        return bypass_user

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exc
        user_id = uuid.UUID(str(sub))
    except (JWTError, ValueError, TypeError):
        raise credentials_exc from None

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == true()))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exc
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
