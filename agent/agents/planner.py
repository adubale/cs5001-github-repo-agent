from agent.models import PlanResult, ReviewResult

class PlannerAgent:
    @staticmethod
    def plan(review: ReviewResult) -> PlanResult:
        if review.risk == "high":
            return PlanResult(
                decision="Create Issue",
                justification="High-risk changes were detected in the review."
            )

        if review.findings:
            return PlanResult(
                decision="Create PR",
                justification="The review found issues or improvements worth documenting."
            )

        return PlanResult(
            decision="No action required",
            justification="No significant issues were found in the review."
        )