from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _clean_dict(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


@dataclass(slots=True)
class StructuredCaseData:
    worker_name: str
    employer_name: str
    issue_type: str
    amount_claimed: int | None
    unpaid_duration_months: int | None
    has_contract: bool | None
    injury_occurred: bool
    raw_text: str
    evidence_items: list[str]
    facts: dict[str, Any] = field(default_factory=dict)
    extraction_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RiskAssessment:
    level: str
    score: int
    evidence_score: int
    priority_for_prosecutor: bool
    priority_label: str
    reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceSummary:
    present_required: list[str]
    missing_required: list[str]
    optional_evidence: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseReport:
    structured_data: StructuredCaseData
    risk_assessment: RiskAssessment
    recommended_actions: list[str]
    legal_basis: list[dict[str, str]]
    evidence: EvidenceSummary

    def to_dict(self) -> dict[str, Any]:
        return {
            "structured_data": self.structured_data.to_dict(),
            "risk_assessment": self.risk_assessment.to_dict(),
            "recommended_actions": list(self.recommended_actions),
            "legal_basis": [dict(item) for item in self.legal_basis],
            "evidence": self.evidence.to_dict(),
        }


@dataclass(slots=True)
class FeedbackMessage:
    sent_at: str
    sender: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(slots=True)
class CaseRecord:
    submission_id: str
    title: str
    source: str
    submitted_at: str
    updated_at: str
    description: str
    report: CaseReport
    facts: dict[str, Any] = field(default_factory=dict)
    user_profile: dict[str, Any] = field(default_factory=dict)
    dispute_profile: dict[str, Any] = field(default_factory=dict)
    evidence_catalog: dict[str, list[str]] = field(default_factory=dict)
    case_status: str = "已受理，待检察评估"
    mediation_priority: str = "待评估"
    prosecution_necessity: str = "待评估"
    relief_checks: dict[str, bool] = field(
        default_factory=lambda: {
            "labor_complaint": False,
            "labor_arbitration": False,
            "legal_aid": False,
            "union_or_street_help": False,
        }
    )
    relief_note: str = ""
    mediation_case_type: str = ""
    prosecution_case_type: str = ""
    prosecutor_note: str = ""
    feedback_messages: list[FeedbackMessage] = field(default_factory=list)
    source_case_id: str | None = None

    @property
    def provided_evidence(self) -> list[str]:
        return list(self.report.structured_data.evidence_items)

    def to_dict(self) -> dict[str, Any]:
        return _clean_dict(
            {
                "submission_id": self.submission_id,
                "source_case_id": self.source_case_id,
                "title": self.title,
                "source": self.source,
                "submitted_at": self.submitted_at,
                "updated_at": self.updated_at,
                "description": self.description,
                "provided_evidence": self.provided_evidence,
                "facts": dict(self.facts),
                "user_profile": dict(self.user_profile),
                "dispute_profile": dict(self.dispute_profile),
                "evidence_catalog": {key: list(value) for key, value in self.evidence_catalog.items()},
                "case_status": self.case_status,
                "mediation_priority": self.mediation_priority,
                "prosecution_necessity": self.prosecution_necessity,
                "relief_checks": dict(self.relief_checks),
                "relief_note": self.relief_note,
                "mediation_case_type": self.mediation_case_type,
                "prosecution_case_type": self.prosecution_case_type,
                "prosecutor_note": self.prosecutor_note,
                "feedback_messages": [item.to_dict() for item in self.feedback_messages],
                "structured_data": self.report.structured_data.to_dict(),
                "risk_assessment": self.report.risk_assessment.to_dict(),
                "recommended_actions": list(self.report.recommended_actions),
                "legal_basis": [dict(item) for item in self.report.legal_basis],
                "evidence": self.report.evidence.to_dict(),
            }
        )
