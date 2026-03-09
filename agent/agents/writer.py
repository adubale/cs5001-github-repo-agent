import json
from agent.llm import OllamaLLM
from agent.models import DraftResult, ReviewResult, PlanResult


class WriterAgent:
    def __init__(self, llm: OllamaLLM | None = None):
        self.llm = llm or OllamaLLM()

    def draft_from_review(self, review: ReviewResult, plan: PlanResult) -> DraftResult:
        decision = plan.decision.strip()

        if decision == "Create Issue":
            return self.draft_issue_from_review(review, plan)
        if decision == "Create PR":
            return self.draft_pr_from_review(review, plan)
        if decision == "No action required":
            raise ValueError("Planner decided no action is required, so no draft should be created.")

        raise ValueError(f"Unsupported planner decision: {decision!r}")

    def draft_issue_from_review(self, review: ReviewResult, plan: PlanResult) -> DraftResult:
        findings_block = self._format_list(review.findings)
        evidence_block = self._format_list(review.evidence)

        prompt=f"""
You are drafting a GitHub Issue for a repository assistant.

Use only the information provided below.
Do not invent repository facts, files, tests, or behavior that are not supported.

Review category: {review.category}
Risk: {review.risk}

Findings:
{findings_block}

Evidence:
{evidence_block}

Planner decision: {plan.decision}
Planner justification: {plan.justification}

Write a GitHub Issue draft with these sections in the body:
- Problem Description
- Evidence
- Acceptance Criteria
- Risk Level

Rules:
- The title must be specific and actionable.
- The body must be concrete and concise.
- Acceptance criteria must be written as a short bullet list.
- Risk Level must clearly state one of: low, medium, high.
- Return JSON only.

Return JSON in exactly this shape:
{{
  "title": "Short issue title",
  "body": "## Problem Description\\n...\\n\\n## Evidence\\n...\\n\\n## Acceptance Criteria\\n- ...\\n\\n## Risk Level\\nmedium"
}}
""".strip()

        return self._generate_structured_draft(prompt)

    def draft_pr_from_review(self, review: ReviewResult, plan: PlanResult) -> DraftResult:
        findings_block = self._format_list(review.findings)
        evidence_block = self._format_list(review.evidence)

        prompt = f"""
You are drafting a GitHub Pull Request for a repository assistant.

Use only the information provided below.
Do not invent repository facts, changed files, tests, or implementation details that are not supported.

Review category: {review.category}
Risk: {review.risk}

Findings:
{findings_block}

Evidence:
{evidence_block}

Planner decision: {plan.decision}
Planner justification: {plan.justification}

Write a GitHub PR draft with these sections in the body:
- Summary
- Files Affected
- Behavior Change
- Test Plan
- Risk Level

Rules:
- The title must be specific and actionable.
- If exact files are unknown, say that exact files should be confirmed before opening the PR.
- If tests are not evidenced, explicitly say tests still need to be added or confirmed.
- Risk Level must clearly state one of: low, medium, high.
- Return JSON only.

Return JSON in exactly this shape:
{{
    "title": "Short PR title",
    "body": "## Summary\\n...\\n\\n## Files Affected\\n...\\n\\n## Behavior Change\\n...\\n\\n## Test Plan\\n...\\n\\n## Risk Level\\nmedium"
}}
""".strip()
        return self._generate_structured_draft(prompt)

    def draft_issue_from_instruction(self, instruction: str) -> DraftResult:
        prompt = f"""
You are drafting a GitHub Issue from an explicit user instruction.

User instruction:
{instruction}

Write a GitHub Issue draft with these sections in the body:
- Problem Description
- Evidence
- Acceptance Criteria
- Risk Level

Rules:
- Do not invent repository-specific facts that are not in the instruction.
- If evidence is not provided, clearly say the issue is based on the user's instruction and needs repository confirmation.
- Acceptance criteria must be a short bullet list.
- Risk Level must clearly state one of: low, medium, high.
- The title must be specific and actionable.
- Return JSON only.

Return JSON in exactly this shape:
{{
  "title": "Short issue title",
  "body": "## Problem Description\\n...\\n\\n## Evidence\\n...\\n\\n## Acceptance Criteria\\n- ...\\n\\n## Risk Level\\nmedium"
}}
""".strip()
        return self._generate_structured_draft(prompt)

    def draft_pr_from_instruction(self, instruction: str) -> DraftResult:
        prompt = f"""
You are drafting a GitHub Pull Request from an explicit user instruction.

User instruction:
{instruction}

Write a GitHub PR draft with these sections in the body:
- Summary
- Files Affected
- Behavior Change
- Test Plan
- Risk Level

Rules:
- Do not invent repository-specific facts that are not in the instruction.
- If exact files are unknown, clearly say they must be confirmed before opening the PR.
- If tests are not provided, explicitly state what should be tested.
- Risk Level must clearly state one of: low, medium, high.
- The title must be specific and actionable.
- Return JSON only.

Return JSON in exactly this shape:
{{
  "title": "Short PR title",
  "body": "## Summary\\n...\\n\\n## Files Affected\\n...\\n\\n## Behavior Change\\n...\\n\\n## Test Plan\\n...\\n\\n## Risk Level\\nmedium"
}}
""".strip()

        return self._generate_structured_draft(prompt)

    def _generate_structured_draft(self, prompt: str) -> DraftResult:
        raw = self.llm.generate(prompt)
        parsed = self._parse_llm_json(raw)
        return self._validated_result(parsed)

    @staticmethod
    def _parse_llm_json(raw: str) -> dict:
        raw = raw.strip()

        if raw.startswith("```"):
            lines = raw.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            raw = "\n".join(lines).strip()

        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in LLM response.")

        return json.loads(raw[start:end + 1])

    @staticmethod
    def _validated_result(parsed: dict) -> DraftResult:
        title = str(parsed.get("title", "")).strip()
        body = str(parsed.get("body", "")).strip()

        if not title:
            raise ValueError("Writer returned an empty title.")
        if not body:
            raise ValueError("Writer returned an empty body.")

        return DraftResult(title=title, body=body)

    @staticmethod
    def _format_list(items: list[str]) -> str:
        if not items:
            return "- None"
        return "\n".join(f"- {item}" for item in items)