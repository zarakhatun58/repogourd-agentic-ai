class JudgeAgent:
    """
    Final reconciliation stage.

    The judge does not inspect arbitrary repository content.
    It operates only on verified evidence-backed candidates.
    """

    def reconcile(
        self,
        verified_items: list[dict],
    ) -> list[dict]:

        final_findings = []

        seen = set()

        for item in verified_items:

            key = (
                item["rule_id"],
                item["file_path"],
                item["line_start"],
            )

            if key in seen:
                continue

            seen.add(key)

            confidence = (
                1.0
                if item["verification_status"] == "verified"
                else 0.0
            )

            final_findings.append(
                {
                    **item,
                    "confidence": confidence,
                    "decision": "accept",
                }
            )

        return final_findings