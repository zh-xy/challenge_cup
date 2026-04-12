from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalysisResult:
    case_type: str
    confidence: float
    matched_keywords: list[str]
    evidence_score: int
    risk_level: str
    recommended_action: str
    reasoning: list[str]
    present_evidence: list[str]
    missing_evidence: list[str]
    optional_evidence: list[str]
    legal_basis: list[dict[str, str]]
    follow_up_steps: list[str]
    raw: dict[str, Any] = field(default_factory=dict)
