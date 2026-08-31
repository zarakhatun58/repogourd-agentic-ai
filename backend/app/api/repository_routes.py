
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.repository import (
    GitHubRepositoryCreate,
    RepositoryResponse,
)
from app.services.repository_service import (
    RepositoryIngestionError,
    ingest_github_repository,
    ingest_zip_repository,
)

router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"],
)


@router.post(
    "/github",
    response_model=RepositoryResponse,
    status_code=201,
)
def ingest_github(
    payload: GitHubRepositoryCreate,
    db: Session = Depends(get_db),
):
    """
    Clone and register a GitHub repository.
    """

    try:
        repository, workspace, commit_sha = ingest_github_repository(
            db=db,
            url=payload.url,
        )

        return repository

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"GitHub ingestion failed: {exc}",
        ) from exc


@router.post(
    "/upload",
    response_model=RepositoryResponse,
    status_code=201,
)
async def upload_repository(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and register a ZIP repository.
    """

    try:
        repository, workspace = await ingest_zip_repository(
            db=db,
            upload=file,
        )

        return repository

    except RepositoryIngestionError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Repository upload failed: {exc}",
        ) from exc


@router.get(
    "",
    response_model=list[RepositoryResponse],
)
def list_repositories(
    db: Session = Depends(get_db),
):
    """
    Return all registered repositories.
    """

    from app.models.repository import Repository

    repositories = (
        db.query(Repository)
        .order_by(Repository.created_at.desc())
        .all()
    )

    return repositories


@router.get(
    "/{repository_id}",
    response_model=RepositoryResponse,
)
def get_repository(
    repository_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get a repository by ID.
    """

    from app.models.repository import Repository

    repository = (
        db.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )

    if not repository:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    return repository

