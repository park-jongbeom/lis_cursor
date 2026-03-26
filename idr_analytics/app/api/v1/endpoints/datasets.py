"""데이터셋 업로드·조회·삭제."""

import json
import uuid
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.crud.crud_dataset import dataset_crud
from app.db.session import get_db
from app.models.dataset import AnalysisDataset
from app.models.user import User
from app.schemas.dataset import DatasetProfileResponse
from app.services.data.ingestion_service import ingestion_service

router = APIRouter()


def _profile_from_row(row: AnalysisDataset) -> DatasetProfileResponse:
    cj = row.columns_json or {}
    cols = cj.get("columns", [])
    dtypes_raw = cj.get("dtypes", {})
    null_raw = cj.get("null_counts", {})
    dtypes = {str(k): str(v) for k, v in dtypes_raw.items()} if isinstance(dtypes_raw, dict) else {}
    null_counts = {str(k): int(v) for k, v in null_raw.items()} if isinstance(null_raw, dict) else {}
    columns = list(cols) if isinstance(cols, list) else []
    return DatasetProfileResponse(
        dataset_id=row.id,
        dataset_name=row.name,
        row_count=row.row_count,
        columns=columns,
        dtypes=dtypes,
        null_counts=null_counts,
        created_at=row.created_at,
    )


class DatasetListItem(BaseModel):
    id: uuid.UUID
    name: str
    dataset_type: str
    row_count: int
    created_at: object


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    summary="CSV 업로드",
    description="multipart로 CSV를 저장하고 `AnalysisDataset` 메타데이터를 생성합니다.",
    response_description="업로드된 데이터셋 프로필(컬럼·dtype·행 수 등)",
)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV 파일"),
    dataset_name: str = Form(..., description="데이터셋 표시 이름"),
    dataset_type: str = Form(..., description="도메인 구분(예: scm, crm, bi)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatasetProfileResponse:
    upload_dir = Path(settings.DATA_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    new_id = uuid.uuid4()
    suffix = Path(file.filename or "data.csv").suffix or ".csv"
    dest = upload_dir / f"{new_id}{suffix}"
    content = await file.read()
    dest.write_bytes(content)
    try:
        df, row_count = ingestion_service.read_csv_validated(str(dest))
    except ValueError as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    profile = ingestion_service.build_columns_profile(df)
    columns_json: dict[str, object] = {
        "columns": profile["columns"],
        "dtypes": profile["dtypes"],
        "null_counts": profile["null_counts"],
    }
    row = await dataset_crud.create(
        db,
        {
            "id": new_id,
            "name": dataset_name,
            "dataset_type": dataset_type,
            "file_path": str(dest.resolve()),
            "row_count": row_count,
            "columns_json": columns_json,
            "profile_json": None,
            "owner_id": current_user.id,
        },
    )
    return _profile_from_row(row)


@router.get(
    "",
    response_model=list[DatasetListItem],
    summary="내 데이터셋 목록",
    description="현재 사용자 소유 데이터셋을 페이지네이션으로 조회합니다.",
    response_description="데이터셋 요약 목록",
)
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> list[DatasetListItem]:
    rows = await dataset_crud.get_multi_by_owner(db, current_user.id, skip=skip, limit=limit)
    return [
        DatasetListItem(
            id=r.id,
            name=r.name,
            dataset_type=r.dataset_type,
            row_count=r.row_count,
            created_at=r.created_at,
        )
        for r in rows
    ]


async def _get_owned_dataset(
    db: AsyncSession,
    dataset_id: uuid.UUID,
    user: User,
) -> AnalysisDataset:
    row = await dataset_crud.get(db, dataset_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    if row.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not owner of this dataset")
    return row


@router.get(
    "/{dataset_id}/preview",
    summary="데이터셋 미리보기",
    description="CSV 상위 N행을 JSON 레코드 배열로 반환합니다.",
    response_description="레코드 배열",
)
async def preview_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20,
) -> list[dict[str, object]]:
    row = await _get_owned_dataset(db, dataset_id, current_user)
    df, _ = ingestion_service.read_csv_validated(row.file_path)
    subset = df.head(limit)
    raw = subset.to_json(orient="records", date_format="iso")
    return cast(list[dict[str, object]], json.loads(raw))


@router.get(
    "/{dataset_id}/profile",
    response_model=DatasetProfileResponse,
    summary="데이터셋 프로필",
    description="컬럼 목록·dtype·null 카운트·생성 시각 등 메타데이터를 반환합니다.",
    response_description="DatasetProfileResponse",
)
async def profile_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatasetProfileResponse:
    row = await _get_owned_dataset(db, dataset_id, current_user)
    return _profile_from_row(row)


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="데이터셋 삭제",
    description="DB 행과 업로드된 파일을 제거합니다. 소유자만 가능합니다.",
    response_description="본문 없음(204)",
)
async def delete_dataset(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    row = await _get_owned_dataset(db, dataset_id, current_user)
    path = Path(row.file_path)
    await dataset_crud.delete(db, id=dataset_id)
    path.unlink(missing_ok=True)
