"""AnalysisDataset CRUD."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.dataset import AnalysisDataset


class CRUDDataset(CRUDBase[AnalysisDataset]):
    async def get_multi_by_owner(
        self,
        db: AsyncSession,
        owner_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AnalysisDataset]:
        result = await db.execute(
            select(AnalysisDataset).where(AnalysisDataset.owner_id == owner_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())


dataset_crud = CRUDDataset(AnalysisDataset)
