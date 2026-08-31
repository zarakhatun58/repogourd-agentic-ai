from fastapi import APIRouter


router = APIRouter(
    prefix="/changelog",
    tags=["Changelog"],
)


CHANGELOG = [
    {
        "version": "0.1.0",
        "date": "2026-08-31",
        "title": "Repository ingestion",
        "description": (
            "Added repository ingestion through ZIP upload and "
            "GitHub repository URL ingestion."
        ),
    },
    {
        "version": "0.1.0",
        "date": "2026-08-31",
        "title": "Deterministic security analysis",
        "description": (
            "Added bounded security rules for Python, JavaScript, "
            "TypeScript, JSX, and TSX source files."
        ),
    },
    {
        "version": "0.1.0",
        "date": "2026-08-31",
        "title": "Evidence-first findings",
        "description": (
            "Security findings now retain source-file, line-range, "
            "matched-content, and verification information."
        ),
    },
    {
        "version": "0.1.0",
        "date": "2026-08-31",
        "title": "Agent trajectory",
        "description": (
            "Added persistent execution traces covering repository "
            "inspection, security analysis, findings, evidence, "
            "and analysis completion."
        ),
    },
    {
        "version": "0.1.0",
        "date": "2026-08-31",
        "title": "Evaluation workflow",
        "description": (
            "Added evaluation endpoints for measuring analysis "
            "quality against the project's evaluation cases."
        ),
    },
]


@router.get("")
def get_changelog():
    return CHANGELOG