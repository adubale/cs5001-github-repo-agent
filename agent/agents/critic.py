import json
from agent.llm import OllamaLLM
from agent.models import DraftResult, ReviewResult, PlanResult, ReflectionResult


class CriticAgent:
    def __init__(self, llm: OllamaLLM | None = None):
        self.llm = llm or OllamaLLM()

    def reflect(self, draft: DraftResult, review: ReviewResult, plan: PlanResult) -> ReflectionResult:
        prompt = self._build_prompt(draft, review, plan)
        raw = self.llm.generate(prompt)
        parsed = self._parse_llm_json(raw)
        return self._validated_result(parsed)

    @staticmethod
    def _build_prompt(draft: DraftResult, review: ReviewResult, plan: PlanResult) -> str:
        findings = "\n".join(f"- {f}" for f in review.findings) if review.findings else "- None"
        evidence = "\n".join(f"- {e}" for e in review.evidence) if review.evidence else "- None"

        return f"""
You are the Critic agent in a GitHub repository assistant.

Your job is to reflect on a drafted Issue or Pull Request and determine whether it is safe and well-supported.

You must check for:

1. Unsupported claims not grounded in the review evidence.
2. Missing evidence references.
3. Missing required sections.
4. Missing test plans (for PRs).
5. Policy violations or hallucinated repository facts.

Review findings:
{findings}

Review evidence:
{evidence}

Planner decision:
{plan.decision}

Draft title:
{draft.title}

Draft body:
{draft.body}

Rules:
- If the draft contains unsupported claims or missing critical sections, verdict = "FAIL".
- If the draft is grounded and complete, verdict = "PASS".
- Notes should describe any problems found.
- Return JSON only.

Return JSON exactly like this:

{{
  "verdict": "PASS",
  "notes": [
    "Draft references evidence correctly."
  ]
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
            raise ValueError("No JSON found in critic output.")

        return json.loads(raw[start:end+1])

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
            notes=notes
        )