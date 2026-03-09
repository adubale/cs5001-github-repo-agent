import json
from agent.models import ReviewResult
from agent.llm import OllamaLLM

class ReviewerAgent:
    def __init__(self, llm: OllamaLLM | None = None):
        self.llm = llm or OllamaLLM()

    def review(self, diff_text: str, changed_files: list[str]) -> ReviewResult:
        grounded_evidence = self._build_grounded_evidence(diff_text, changed_files)
        prompt = self._build_prompt(diff_text, changed_files, grounded_evidence)

        raw = self.llm.generate(prompt)
        parsed = self._parse_llm_json(raw)
        return self._validated_result(parsed, grounded_evidence)

    @staticmethod
    def _build_grounded_evidence(diff_text: str, changed_files: list[str]) -> list[str]:
        evidence = []

        if changed_files:
            evidence.append(f"{len(changed_files)} file(s) changed.")
            for path in changed_files:
                evidence.append(f"Changed file: {path}")
        else:
            evidence.append("No changed files detected.")

        diff_lower = diff_text.lower()

        if "test" in diff_lower or any("test" in p.lower() for p in changed_files):
            evidence.append("Test-related content appears in the diff or filenames.")
        else:
            evidence.append("No obvious test-related changes detected.")

        sensitive_keyword = {
            "auth": "Authentication or authorization logic appears to be affected.",
            "login": "Login-related logic appears to be affected.",
            "payment": "Payment-related logic seems to be affected.",
            "api": "API-related code appears to be affected.",
            "config": "Configuration-related code appears to be affected.",
            "migration": "Database migration-related code appears to be affected.",
            "schema": "Schema-related code appears to be affected.",
            "security": "Security-related code appears to be affected.",
        }

        for keyword, message in sensitive_keyword.items():
            if keyword in diff_lower or any(keyword in p.lower() for p in changed_files):
                evidence.append(message)

        return evidence

    @staticmethod
    def _build_prompt(
            diff_text: str,
            changed_files: list[str],
            grounded_evidence: list[str]
    ) -> str:
        file_block = "\n".join(f"- {path}" for path in changed_files) if changed_files else "- None"
        evidence_block = "\n".join(f"- {item}" for item in grounded_evidence)

        truncated_diff = diff_text[:8000] if diff_text else "[no diff provided]"

        return f"""
        You are a code review agent for a GitHub repository assistant.

        Your task is to review the repository diff and return a structured review result.

        You must classify:
        - category: one of ["feature", "bugfix", "refactor", "docs", "test", "chore"]
        - risk: one of ["low", "medium", "high"]

        You must also provide:
        - findings: short reviewer observations
        - evidence: concrete evidence grounded in the changed files, diff, or repository context

        Rules:
        - Do not invent files, behaviors, or tests.
        - Evidence must be concrete and tied to the supplied context.
        - High risk should be used for authentication, payments, security-sensitive logic, database/schema changes, or broad infrastructure/config changes.
        - Medium risk should be used for API changes, validation changes, non-trivial business logic, or changes touching several files without clear tests.
        - Low risk should be used for localized, low-impact, well-bounded changes.
        - Return JSON only. No prose outside JSON.

        Changed files:
        {file_block}

        Precomputed evidence:
        {evidence_block}

        Diff:
        {truncated_diff}

        Return JSON in exactly this shape:
        {{
          "category": "feature",
          "risk": "medium",
          "findings": [
            "..."
          ],
          "evidence": [
            "..."
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
            raise ValueError("No JSON object found in LLM response.")

        return json.loads(raw[start:end + 1])

    @staticmethod
    def _validated_result(parsed: dict, grounded_evidence: list[str]) -> ReviewResult:
        allowed_categories = {"feature", "bugfix", "refactor", "docs", "test", "chore"}
        allowed_risks = {"low", "medium", "high"}

        category = str(parsed.get("category", "refactor")).lower().strip()
        risk = str(parsed.get("risk", "medium")).lower().strip()

        if category not in allowed_categories:
            category = "refactor"
        if risk not in allowed_risks:
            risk = "medium"

        findings = parsed.get("findings", [])
        evidence = parsed.get("evidence", [])

        if not isinstance(findings, list):
            findings = [str(findings)]
        if not isinstance(evidence, list):
            evidence = [str(evidence)]

        findings = [str(f).strip() for f in findings if str(f).strip()]
        evidence = [str(e).strip() for e in evidence if str(e).strip()]

        merged_evidence = grounded_evidence[:]
        for item in evidence:
            if item not in merged_evidence:
                merged_evidence.append(item)

        return ReviewResult(
            category=category,
            risk=risk,
            findings=findings,
            evidence=merged_evidence
        )