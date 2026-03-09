import json
from agent.llm import OllamaLLM
from agent.models import DraftResult, ReviewResult, PlanResult, ReflectionResult


class CriticAgent:
    def __init__(self, llm: OllamaLLM | None = None):
        self.llm = llm or OllamaLLM()

    def reflect_from_review(
        self,
        draft: DraftResult,
        review: ReviewResult,
        plan: PlanResult,
    ) -> ReflectionResult:
        prompt = self._build_review_prompt(draft, review, plan)
        raw = self.llm.generate(prompt)
        parsed = self._parse_llm_json(raw)
        return self._validated_result(parsed)

    def reflect_from_instruction(
        self,
        draft: DraftResult,
        instruction: str,
        target: str,
    ) -> ReflectionResult:
        prompt = self._build_instruction_prompt(draft, instruction, target)
        raw = self.llm.generate(prompt)
        parsed = self._parse_llm_json(raw)
        return self._validated_result(parsed)

    @staticmethod
    def _build_review_prompt(
        draft: DraftResult,
        review: ReviewResult,
        plan: PlanResult,
    ) -> str:
        findings = "\n".join(f"- {f}" for f in review.findings) if review.findings else "- None"
        evidence = "\n".join(f"- {e}" for e in review.evidence) if review.evidence else "- None"

        return f"""
You are the Critic agent in a GitHub repository assistant.

Your job is to reflect on a drafted GitHub Issue or Pull Request produced from repository review data.

You must check for:
1. Unsupported claims not grounded in the review evidence.
2. Missing evidence references.
3. Missing required sections.
4. Missing tests or missing test plan when relevant.
5. Policy violations or hallucinated repository facts.
6. Whether the draft matches the planner decision.

Review findings:
{findings}

Review evidence:
{evidence}

Planner decision:
{plan.decision}

Planner justification:
{plan.justification}

Draft title:
{draft.title}

Draft body:
{draft.body}

Rules:
- If the draft contains unsupported claims, verdict = "FAIL".
- If the draft is missing important required sections, verdict = "FAIL".
- If the draft conflicts with the review evidence or planner decision, verdict = "FAIL".
- If the draft is grounded and complete enough, verdict = "PASS".
- Notes should be short and specific.
- Return JSON only.

Return JSON exactly like this:
{{
  "verdict": "PASS",
  "notes": [
    "Draft is grounded in the review evidence."
  ]
}}
""".strip()

    @staticmethod
    def _build_instruction_prompt(
        draft: DraftResult,
        instruction: str,
        target: str,
    ) -> str:
        normalized_target = target.strip().lower()

        if normalized_target == "issue":
            required_sections = """
Required body sections:
- Problem Description
- Evidence
- Acceptance Criteria
- Risk Level
""".strip()
        elif normalized_target == "pr":
            required_sections = """
Required body sections:
- Summary
- Files Affected
- Behavior Change
- Test Plan
- Risk Level
""".strip()
        else:
            raise ValueError("target must be either 'issue' or 'pr'")

        return f"""
You are the Critic agent in a GitHub repository assistant.

Your job is to reflect on a drafted GitHub {normalized_target.upper()} produced from an explicit user instruction.

You must check for:
1. Whether the draft actually follows the user's instruction.
2. Missing required sections.
3. Internal contradictions.
4. Hallucinated repository-specific facts not supported by the instruction.
5. Missing tests or vague test plan when relevant.
6. Overly vague or non-actionable wording.

User instruction:
{instruction}

{required_sections}

Draft title:
{draft.title}

Draft body:
{draft.body}

Rules:
- Do not require repository evidence that was never provided.
- If the draft invents repository-specific files, implementation details, tests, or behavior not present in the instruction, verdict = "FAIL".
- If the draft misses important required sections, verdict = "FAIL".
- If the draft follows the instruction and stays appropriately cautious, verdict = "PASS".
- Notes should be short and specific.
- Return JSON only.

Return JSON exactly like this:
{{
  "verdict": "PASS",
  "notes": [
    "Draft follows the instruction and avoids unsupported repository claims."
  ]
}}
""".strip()

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
            raise ValueError("No JSON found in critic output.")

        return json.loads(raw[start:end + 1])

    @staticmethod
    def _validated_result(parsed: dict) -> ReflectionResult:
        verdict = str(parsed.get("verdict", "FAIL")).strip().upper()
        notes = parsed.get("notes", [])

        if verdict not in {"PASS", "FAIL"}:
            verdict = "FAIL"

        if not isinstance(notes, list):
            notes = [str(notes)]

        notes = [str(n).strip() for n in notes if str(n).strip()]

        return ReflectionResult(
            verdict=verdict,
            notes=notes,
        )