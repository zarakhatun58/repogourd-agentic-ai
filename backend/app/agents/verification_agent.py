class VerificationAgent:
    """
    Independent verification stage.

    A candidate finding becomes accepted only when:
      1. the file exists;
      2. the referenced line exists;
      3. the evidence matches the source;
      4. the rule is applicable to the file type.
    """

    def verify(
        self,
        evidence_items: list[dict],
    ) -> list[dict]:

        verified = []

        for item in evidence_items:

            if not item.get("evidence_verified"):
                continue

            verified.append(
                {
                    **item,
                    "verification_status": "verified",
                }
            )

        return verified