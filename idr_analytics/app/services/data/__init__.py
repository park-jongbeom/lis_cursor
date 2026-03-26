"""Data services."""

from __future__ import annotations

from app.services.data.ingestion_service import IngestionService, ingestion_service
from app.services.data.preprocessing_service import PreprocessingService, preprocessing_service

__all__ = [
    "IngestionService",
    "PreprocessingService",
    "ingestion_service",
    "preprocessing_service",
]
