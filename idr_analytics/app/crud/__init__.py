"""CRUD package — re-export singletons."""

from __future__ import annotations

from app.crud.crud_dataset import CRUDDataset, dataset_crud
from app.crud.crud_user import CRUDUser, user_crud

__all__ = [
    "CRUDDataset",
    "CRUDUser",
    "dataset_crud",
    "user_crud",
]
