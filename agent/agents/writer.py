from agent.llm import OllamaLLM
from agent.models import DraftResult, ReviewResult, PlanResult

class WriterAgent:
    def __init__(self, model: str = "devstral-small-2:24b-cloud"):
        self.llm = OllamaLLM(model=model)

    def draft_issue(self, review: ReviewResult, plan: PlanResult) -> DraftResult:
        prompt = f"""
You are drafting a GitHub Issue.

Review category: {review.category}
Risk: {review.risk}
Findings: {review.findings}
Evidence: {review.evidence}
Planner decision: {plan.decision}
Planner justification: {plan.justification}

Write a GitHub issue with these sections:

Title
Problem Description
Evidence
Acceptance Criteria
Risk Level

Be concrete and concise.
"""

        body = self.llm.generate(prompt).strip()

        return DraftResult(
            title="AI Generated Issue Draft",
            body=body,
        )