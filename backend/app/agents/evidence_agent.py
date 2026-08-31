from pathlib import Path


class EvidenceAgent:
    """
    Converts candidate findings into source-backed evidence.

    The agent does not invent evidence.
    Evidence must come directly from the repository.
    """

    def collect(
        self,
        workspace: Path,
        candidates: list[dict],
    ) -> list[dict]:

        verified_evidence = []

        for candidate in candidates:

            file_path = (
                workspace /
                candidate["file_path"]
            )

            try:
                lines = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).splitlines()
            except Exception:
                continue

            line_number = candidate["line_start"]

            if line_number < 1:
                continue

            if line_number > len(lines):
                continue

            actual_line = lines[line_number - 1]

            verified_evidence.append(
                {
                    **candidate,
                    "evidence_content": actual_line.strip(),
                    "evidence_verified": (
                        candidate["matched_text"].lower()
                        in actual_line.lower()
                    ),
                }
            )

        return verified_evidence