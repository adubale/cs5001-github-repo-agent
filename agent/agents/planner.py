import json
from agent.models import PlanResult, ReviewResult
from agent.llm import OllamaLLM

class PlannerAgent:
    def __init__(self, llm: OllamaLLM | None = None):
        self.llm = llm or OllamaLLM()

    def plan(self, review: ReviewResult) -> PlanResult:
        prompt = self._build_prompt(review)
        raw = self.llm.generate(prompt)
        parsed = self._parse_llm_json(raw)
        return self._validated_result(parsed)

    @staticmethod
    def _build_prompt(review: ReviewResult) -> str:
        findings_block = "\n".join(f"- {f}" for f in review.findings) if review.findings else "- None"
        evidence_block = "\n".join(f"- {e}" for e in review.evidence) if review.evidence else "- None"

        return f"""
You are a planning agent for a GitHub repository assistant.

You are given a structured review result. Your job is to decide the next action.

Allowed decisions:
- "Create Issue"
- "Create PR"
- "No action required"

Review result:
Category: {review.category}
Risk: {review.risk}

Findings:
{findings_block}

Evidence:
{evidence_block}

Rules:
- Base your decision only on the supplied review result.
- Do not invent evidence.
- Use "Create Issue" when the review suggests a problem, risk, missing evidence, missing tests, or follow-up work that should be tracked.
- Use "Create PR" when the review suggests a concrete improvement or change proposal that is actionable and ready to draft.
- Use "Create PR" if a feature has been added and there are no further issues
- Use "No action required" when the review indicates no meaningful follow-up is needed.
- The justification must explicitly reference the review evidence or findings.
- Return JSON only.

Return JSON in exactly this shape:
{{
  "decision": "Create Issue",
  "justification": "The review identified ... Evidence includes ..."
}}
""".strip()

    @staticmethod
    def _parse_llm_json(raw: str) -> dict:
        raw = raw.strip()

        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in LLM response.")

        return json.loads(raw[start:end + 1])

    @staticmethod
    def _validated_result(parsed: dict) -> PlanResult:
        allowed_decisions = {"Create Issue", "Create PR", "No action required"}

        decision = str(parsed.get("decision", "No action required")).strip()
        justification = str(parsed.get("justification", "")).strip()

        if decision not in allowed_decisions:
            raise ValueError(f"Invalid planner decision: {decision!r}")

        if not justification:
            raise ValueError("Planner returned an empty justification.")

        return PlanResult(decision=decision, justification=justification)

"""
    
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
"""