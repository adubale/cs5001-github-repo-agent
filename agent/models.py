from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class ReviewResult:
    category: str
    risk: str
    findings: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

@dataclass
class PlanResult:
    decision: str
    justification: str

@dataclass
class DraftResult:
    title: str
    body: str

@dataclass
class ReflectionResult:
    verdict: str
    notes: list[str] = field(default_factory=list)

@dataclass
class DraftArtifact:
    id: str
    kind: str
    source: str
    title: str
    body: str
    status: str

    review_result: Optional[ReviewResult] = None
    plan_result: Optional[PlanResult] = None
    reflection_result: Optional[ReflectionResult] = None

    github_number: Optional[int] = None
    github_url: Optional[str] = None
    github_error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "DraftArtifact":
        review_result = data.get("review_result")
        if review_result is not None:
            review_result = ReviewResult(**review_result)

        plan_result = data.get("plan_result")
        if plan_result is not None:
            plan_result = PlanResult(**plan_result)

        reflection_result = data.get("reflection_result")
        if reflection_result is not None:
            reflection_result = ReflectionResult(**reflection_result)

        return cls(
            id=data["id"],
            kind=data["kind"],
            source=data["source"],
            title=data["title"],
            body=data["body"],
            status=data["status"],
            review_result=review_result,
            plan_result=plan_result,
            reflection_result=reflection_result,
            github_number=data.get("github_number"),
            github_url=data.get("github_url"),
            github_error=data.get("github_error"),
        )

@dataclass
class ReviewArtifact:
    id: str
    category: str
    risk: str
    findings: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    plan_result: Optional[PlanResult] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ReviewArtifact":
        plan_result = data.get("plan_result")
        if plan_result is not None:
            plan_result = PlanResult(**plan_result)

        return cls(
            id=data["id"],
            category=data["category"],
            risk=data["risk"],
            findings=data.get("findings", []),
            evidence=data.get("evidence", []),
            plan_result=plan_result,
        )