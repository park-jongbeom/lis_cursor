"""Generic async CRUD base (SQLAlchemy 2.0)."""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel
from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class CRUDBase(Generic[ModelT]):
    """create/update/delete 후 commit + refresh 통일."""

    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    async def get(self, db: AsyncSession, id: uuid.UUID) -> ModelT | None:
        # User / AnalysisDataset 등 PK `id` 보유 모델 전제 (DeclarativeBase만으로는 mypy가 `id` 추론 불가)
        result = await db.execute(select(self.model).where(self.model.id == id))  # type: ignore[attr-defined]
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> list[ModelT]:
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj_in: dict[str, Any] | BaseModel) -> ModelT:
        data = obj_in.model_dump() if isinstance(obj_in, BaseModel) else dict(obj_in)
        db_obj = self.model(**data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelT,
        obj_in: dict[str, Any] | BaseModel,
    ) -> ModelT:
        data = obj_in.model_dump(exclude_unset=True) if isinstance(obj_in, BaseModel) else dict(obj_in)
        for field, value in data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: uuid.UUID) -> None:
        result = await db.execute(sa_delete(self.model).where(self.model.id == id))  # type: ignore[attr-defined]
        await db.commit()
        cr = cast(CursorResult[Any], result)
        if cr.rowcount == 0:
            msg = f"{self.model.__name__} with id {id} not found"
            raise ValueError(msg)
