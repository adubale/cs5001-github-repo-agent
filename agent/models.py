from dataclasses import dataclass, field

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
