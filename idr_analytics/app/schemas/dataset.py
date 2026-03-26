"""Dataset upload and profile DTOs."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DatasetUploadRequest(BaseModel):
    dataset_name: str
    dataset_type: str  # "scm" | "crm" | "bi"


class DatasetProfileResponse(BaseModel):
    """ORM `AnalysisDataset` 매핑: id/name → dataset_id/dataset_name, 나머지는 프로필 채움 후 확장."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    dataset_id: uuid.UUID = Field(validation_alias="id")
    dataset_name: str = Field(validation_alias="name")
    row_count: int
    columns: list[str] = Field(default_factory=list)
    dtypes: dict[str, str] = Field(default_factory=dict)
    null_counts: dict[str, int] = Field(default_factory=dict)
    created_at: datetime
