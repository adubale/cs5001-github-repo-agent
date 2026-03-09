import json
from agent.llm import OllamaLLM


class ImproverAgent:
    def __init__(self, llm: OllamaLLM | None = None):
        self.llm = llm or OllamaLLM()

    def improve_issue(self, title: str, body: str | None) -> dict:
        prompt = f"""
You are an agent improving an existing GitHub Issue.

You must do two things in order:
1. Critique the existing issue.
2. Suggest an improved structured version.

Your critique must identify:
- unclear or missing information
- vague language
- weak or missing acceptance criteria

Then produce:
- suggested_acceptance_criteria
- improved_title
- improved_body

Rules:
- Do not invent repository-specific facts not supported by the issue text.
- If evidence is missing, explicitly say so.
- The improved issue body must use exactly these sections:
  - Problem Description
  - Evidence
  - Acceptance Criteria
  - Risk Level
- Acceptance criteria must be concrete and testable.
- Risk Level must clearly state one of: low, medium, high.
- Return JSON only.

Original Issue Title:
{title}

Original Issue Body:
{body or ""}

Return JSON in exactly this shape:
{{
  "critique": [
    "..."
  ],
  "suggested_acceptance_criteria": [
    "..."
  ],
  "improved_title": "Improved issue title",
  "improved_body": "## Problem Description\\n...\\n\\n## Evidence\\n...\\n\\n## Acceptance Criteria\\n- ...\\n\\n## Risk Level\\nmedium"
}}
""".strip()

        raw = self.llm.generate(prompt)
        parsed = self._parse_llm_json(raw)
        return self._validated_result(parsed)

    def improve_pr(self, title: str, body: str | None) -> dict:
        prompt = f"""
You are an agent improving an existing GitHub Pull Request description.

You must do two things in order:
1. Critique the existing PR description.
2. Suggest an improved structured version.

Your critique must identify:
- unclear or missing information
- vague language
- weak or missing acceptance criteria
- missing test plan or behavior-change detail

Then produce:
- suggested_acceptance_criteria
- improved_title
- improved_body

Rules:
- Do not invent repository-specific facts not supported by the PR text.
- If files or tests are not specified, explicitly say they still need confirmation.
- The improved PR body must use exactly these sections:
  - Summary
  - Files Affected
  - Behavior Change
  - Test Plan
  - Acceptance Criteria
  - Risk Level
- Acceptance criteria must be concrete and testable.
- Risk Level must clearly state one of: low, medium, high.
- Return JSON only.

Original PR Title:
{title}

Original PR Body:
{body or ""}

Return JSON in exactly this shape:
{{
  "critique": [
    "..."
  ],
  "suggested_acceptance_criteria": [
    "..."
  ],
  "improved_title": "Improved PR title",
  "improved_body": "## Summary\\n...\\n\\n## Files Affected\\n...\\n\\n## Behavior Change\\n...\\n\\n## Test Plan\\n...\\n\\n## Acceptance Criteria\\n- ...\\n\\n## Risk Level\\nmedium"
}}
""".strip()

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
    def _validated_result(parsed: dict) -> dict:
        critique = parsed.get("critique", [])
        suggested_acceptance_criteria = parsed.get("suggested_acceptance_criteria", [])
        improved_title = str(parsed.get("improved_title", "")).strip()
        improved_body = str(parsed.get("improved_body", "")).strip()

        if not isinstance(critique, list):
            critique = [str(critique)]
        if not isinstance(suggested_acceptance_criteria, list):
            suggested_acceptance_criteria = [str(suggested_acceptance_criteria)]

        critique = [str(item).strip() for item in critique if str(item).strip()]
        suggested_acceptance_criteria = [
            str(item).strip()
            for item in suggested_acceptance_criteria
            if str(item).strip()
        ]

        if not critique:
            critique = ["The original artifact needs clearer structure and more concrete detail."]

        if not improved_title:
            raise ValueError("Improver returned an empty improved_title.")
        if not improved_body:
            raise ValueError("Improver returned an empty improved_body.")

        return {
            "critique": critique,
            "suggested_acceptance_criteria": suggested_acceptance_criteria,
            "improved_title": improved_title,
            "improved_body": improved_body,
        }