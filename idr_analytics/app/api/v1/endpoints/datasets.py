"""데이터셋 업로드·조회·삭제."""

import csv
import json
import shutil
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


class SampleDatasetItem(BaseModel):
    sample_file: str
    dataset_type: str
    columns: list[str]
    preview_rows: list[dict[str, str]]


class SampleUploadRequest(BaseModel):
    sample_file: str
    dataset_name: str | None = None
    dataset_type: str | None = None


SAMPLE_FILES: dict[str, str] = {
    "bi_from_lis.csv": "bi",
    "crm_from_lis.csv": "crm",
    "scm_from_lis.csv": "scm",
    "mixed_from_lis.csv": "mixed",
    # 문서·통합 테스트·구 데모 HTML 습관과 동일 파일명 (리포 demo/sample_data 에 존재)
    "scm_sample.csv": "scm",
    "crm_sample.csv": "crm",
    "bi_sample.csv": "bi",
}


def _sample_data_dir() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "demo" / "sample_data"
        if candidate.exists():
            return candidate
    return current.parents[3] / "demo" / "sample_data"


def _sample_catalog() -> list[SampleDatasetItem]:
    base = _sample_data_dir()
    items: list[SampleDatasetItem] = []
    for file_name, dataset_type in SAMPLE_FILES.items():
        path = base / file_name
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            columns = list(reader.fieldnames or [])
            preview_rows: list[dict[str, str]] = []
            for idx, row in enumerate(reader):
                if idx >= 3:
                    break
                preview_rows.append({str(k): str(v) for k, v in row.items() if k is not None})
        items.append(
            SampleDatasetItem(
                sample_file=file_name,
                dataset_type=dataset_type,
                columns=columns,
                preview_rows=preview_rows,
            )
        )
    return items


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
    "/sample-catalog",
    response_model=list[SampleDatasetItem],
    summary="데모 샘플 목록",
    description="내장 샘플 CSV 목록과 컬럼/미리보기(상위 3행)를 반환합니다.",
    response_description="샘플 파일 메타데이터 목록",
)
async def sample_catalog(
    current_user: User = Depends(get_current_user),
) -> list[SampleDatasetItem]:
    del current_user
    return _sample_catalog()


@router.post(
    "/upload-sample",
    status_code=status.HTTP_201_CREATED,
    summary="내장 샘플 업로드",
    description="서버 내 demo/sample_data의 샘플 CSV를 선택해 즉시 데이터셋으로 등록합니다.",
    response_description="업로드된 데이터셋 프로필",
)
async def upload_sample_dataset(
    body: SampleUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatasetProfileResponse:
    sample_file = body.sample_file.strip()
    if sample_file not in SAMPLE_FILES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="지원하지 않는 샘플 파일입니다.")
    source = _sample_data_dir() / sample_file
    if not source.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="샘플 파일을 찾을 수 없습니다.")

    upload_dir = Path(settings.DATA_UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    new_id = uuid.uuid4()
    suffix = source.suffix or ".csv"
    dest = upload_dir / f"{new_id}{suffix}"
    shutil.copyfile(source, dest)

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
            "name": (body.dataset_name or source.stem).strip() or source.stem,
            "dataset_type": (body.dataset_type or SAMPLE_FILES[sample_file]).strip(),
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
