from agent.models import ReviewResult


class ReviewerAgent:
    @staticmethod
    def review(diff_text: str, changed_files: list[str]) -> ReviewResult:
        diff_lower = diff_text.lower()

        category = "refactor"
        risk = "low"

        findings = []
        evidence = []

        # Detect category
        if "fix" in diff_lower or "bug" in diff_lower:
            category = "bugfix"

        elif "feat" in diff_lower or "feature" in diff_lower:
            category = "feature"

        # Detect risk
        if "auth" in diff_lower or "login" in diff_lower or "payment" in diff_lower:
            risk = "high"

        elif "validation" in diff_lower or "api" in diff_lower:
            risk = "medium"

        # Evidence from changed files
        for path in changed_files:
            evidence.append(f"Changed file: {path}")

        # Simple heuristic finding
        if "test" not in diff_lower:
            findings.append("No obvious test-related changes detected.")
            evidence.append("Diff does not contain test changes.")

        return ReviewResult(
            category=category,
            risk=risk,
            findings=findings,
            evidence=evidence
        )