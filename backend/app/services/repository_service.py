import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path

from fastapi import UploadFile
from git import Repo
from sqlalchemy.orm import Session

from app.models.repository import Repository


# ============================================================
# Safety limits
# ============================================================

MAX_ZIP_SIZE = 100 * 1024 * 1024          # 100 MB
MAX_EXTRACTED_FILES = 20_000
MAX_EXTRACTED_SIZE = 500 * 1024 * 1024    # 500 MB


class RepositoryIngestionError(Exception):
    """Raised when repository ingestion fails."""


# ============================================================
# Windows-safe filesystem cleanup
# ============================================================

def _remove_readonly(func, path, exc_info):
    """
    Windows-safe callback for shutil.rmtree().

    Git repositories can contain read-only files, especially
    files inside .git/objects/pack.
    """

    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        # Do not hide the original cleanup error.
        raise


def _cleanup_workspace(workspace: Path) -> None:
    """
    Safely remove a temporary repository workspace.

    Handles Windows read-only Git files.
    """

    if not workspace.exists():
        return

    try:
        shutil.rmtree(
            workspace,
            onerror=_remove_readonly,
            ignore_errors=False,
        )
    except Exception:
        # Best effort cleanup.
        # We don't want a cleanup failure to hide the
        # original ingestion problem.
        pass


# ============================================================
# ZIP safety
# ============================================================

def _safe_extract_zip(
    zip_path: Path,
    destination: Path,
) -> None:
    """
    Safely extract a ZIP archive.

    Protects against:

    - absolute paths
    - ../ path traversal
    - excessive file count
    - excessive extracted size
    """

    destination = destination.resolve()

    total_size = 0
    file_count = 0

    with zipfile.ZipFile(zip_path, "r") as archive:

        # ----------------------------------------------------
        # Validate entire archive first
        # ----------------------------------------------------

        for member in archive.infolist():

            file_count += 1

            if file_count > MAX_EXTRACTED_FILES:
                raise RepositoryIngestionError(
                    "ZIP contains too many files."
                )

            member_path = Path(member.filename)

            # Reject absolute paths
            if member_path.is_absolute():
                raise RepositoryIngestionError(
                    f"Unsafe absolute ZIP path: {member.filename}"
                )

            # Resolve destination path
            target = (
                destination / member.filename
            ).resolve()

            # Prevent ../ traversal
            try:
                target.relative_to(destination)
            except ValueError as exc:
                raise RepositoryIngestionError(
                    f"Unsafe ZIP path: {member.filename}"
                ) from exc

            # Directories do not contribute to extracted size
            if member.is_dir():
                continue

            total_size += member.file_size

            if total_size > MAX_EXTRACTED_SIZE:
                raise RepositoryIngestionError(
                    "ZIP extracted size exceeds the allowed limit."
                )

        # ----------------------------------------------------
        # Extract after validation
        # ----------------------------------------------------

        for member in archive.infolist():

            target = (
                destination / member.filename
            ).resolve()

            if member.is_dir():

                target.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                continue

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with archive.open(member, "r") as source:
                with target.open("wb") as target_file:

                    shutil.copyfileobj(
                        source,
                        target_file,
                    )


# ============================================================
# Git metadata
# ============================================================

def _get_git_metadata(
    repo_path: Path,
) -> tuple[str | None, str]:

    """
    Return:

        commit SHA
        current/default branch
    """

    git_path = repo_path / ".git"

    # ZIP repositories normally do not contain .git
    if not git_path.exists():
        return None, "main"

    try:

        repo = Repo(
            repo_path,
            search_parent_directories=False,
        )

        commit_sha = repo.head.commit.hexsha

        try:
            branch = repo.active_branch.name
        except Exception:
            branch = "main"

        return commit_sha, branch

    except Exception:

        return None, "main"


# ============================================================
# Repository name
# ============================================================

def _repository_name_from_url(url: str) -> str:

    name = url.rstrip("/").split("/")[-1]

    if name.endswith(".git"):
        name = name[:-4]

    if not name:
        name = "repository"

    return name


# ============================================================
# GitHub ingestion
# ============================================================

def ingest_github_repository(
    db: Session,
    url: str,
) -> tuple[Repository, Path, str | None]:
    """
    Clone a GitHub repository into a persistent RepoGuard
    workspace and create/update a Repository database row.
    """

    if not url:
        raise RepositoryIngestionError(
            "GitHub repository URL is required."
        )

    # ---------------------------------
    # Determine repository name
    # ---------------------------------

    name = url.rstrip("/").split("/")[-1]

    if name.endswith(".git"):
        name = name[:-4]

    if not name:
        name = "repository"

    # ---------------------------------
    # Persistent workspace
    # ---------------------------------

    backend_root = Path(__file__).resolve().parents[2]

    repositories_root = (
        backend_root / "storage" / "repositories"
    )

    repositories_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Use repository name as workspace directory.
    clone_path = repositories_root / name

    # ---------------------------------
    # Remove previous clone if present
    # ---------------------------------

    if clone_path.exists():
        shutil.rmtree(
            clone_path,
            ignore_errors=True,
        )

    try:

        # ---------------------------------
        # Clone GitHub repository
        # ---------------------------------

        Repo.clone_from(
            url,
            clone_path,
            depth=1,
        )

        # ---------------------------------
        # Get Git metadata
        # ---------------------------------

        commit_sha, branch = _get_git_metadata(
            clone_path
        )

        # ---------------------------------
        # Save repository in PostgreSQL
        # ---------------------------------

        repository = Repository(
            name=name,
            source_type="github",
            source_url=url,
            default_branch=branch,
            workspace_path=str(clone_path),
            latest_commit_sha=commit_sha,
        )

        db.add(repository)

        db.commit()

        db.refresh(repository)

        return (
            repository,
            clone_path,
            commit_sha,
        )

    except Exception as exc:

        db.rollback()

        # Only remove the persistent workspace when
        # ingestion itself fails.
        if clone_path.exists():
            shutil.rmtree(
                clone_path,
                ignore_errors=True,
            )

        raise RepositoryIngestionError(
            f"GitHub repository ingestion failed: {exc}"
        ) from exc



# ============================================================
# ZIP ingestion
# ============================================================

async def ingest_zip_repository(
    db: Session,
    upload: UploadFile,
) -> tuple[Repository, Path]:

    """
    Safely upload and extract a ZIP repository.

    Returns:

        repository
        extracted repository path
    """

    # --------------------------------------------------------
    # Validate filename
    # --------------------------------------------------------

    if not upload.filename:

        raise RepositoryIngestionError(
            "ZIP filename is required."
        )

    if not upload.filename.lower().endswith(".zip"):

        raise RepositoryIngestionError(
            "Only ZIP files are supported."
        )

    # --------------------------------------------------------
    # Create temporary workspace
    # --------------------------------------------------------

    workspace = Path(
        tempfile.mkdtemp(
            prefix="repoguard-repo-"
        )
    )

    zip_path = workspace / "upload.zip"

    extract_path = workspace / "repository"

    try:

        # ----------------------------------------------------
        # Read upload
        # ----------------------------------------------------

        content = await upload.read()

        # ----------------------------------------------------
        # Check upload size
        # ----------------------------------------------------

        if len(content) > MAX_ZIP_SIZE:

            raise RepositoryIngestionError(
                "ZIP file exceeds the 100 MB upload limit."
            )

        # ----------------------------------------------------
        # Save ZIP
        # ----------------------------------------------------

        zip_path.write_bytes(content)

        extract_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # Safe extraction
        # ----------------------------------------------------

        _safe_extract_zip(
            zip_path,
            extract_path,
        )

        # ----------------------------------------------------
        # Repository name
        # ----------------------------------------------------

        name = Path(
            upload.filename
        ).stem

        # ----------------------------------------------------
        # Save repository
        # ----------------------------------------------------

        repository = Repository(
            name=name,
            source_type="zip",
            source_url=None,
            default_branch="main",
            workspace_path=str(extract_path),
            latest_commit_sha=None,
        )

        db.add(repository)

        db.commit()

        db.refresh(repository)

        return (
            repository,
            extract_path,
        )

    except Exception as exc:

        db.rollback()

        _cleanup_workspace(workspace)

        raise RepositoryIngestionError(
            f"ZIP repository ingestion failed: {exc}"
        ) from exc