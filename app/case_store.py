from __future__ import annotations

from datetime import datetime
from typing import Any

from app.data_processor import DataProcessor
from core.knowledge_base import KnowledgeBase


class CaseStore:
    def __init__(self, kb: KnowledgeBase, processor: DataProcessor) -> None:
        self.kb = kb
        self.processor = processor
        self._cases: list[dict[str, Any]] = []
        self._counter = 1
        self._seed_demo_cases()

    def list_samples(self) -> list[dict[str, Any]]:
        return self.kb.sample_cases

    def list_submissions(self) -> list[dict[str, Any]]:
        return list(self._cases)

    def get_all_cases(self) -> list[dict[str, Any]]:
        return self.list_submissions()

    def submit_case(
        self,
        description: str,
        provided_evidence: list[str] | None = None,
        facts: dict[str, Any] | None = None,
        title: str | None = None,
        source: str = "manual",
        source_case_id: str | None = None,
        user_profile: dict[str, Any] | None = None,
        dispute_profile: dict[str, Any] | None = None,
        evidence_catalog: dict[str, list[str]] | None = None,
    ) -> dict[str, Any]:
        facts = facts or {}
        user_profile = user_profile or {}
        dispute_profile = dispute_profile or {}
        evidence_catalog = evidence_catalog or {}
        merged_evidence = self._merge_evidence_catalog(provided_evidence, evidence_catalog)
        report = self.processor.build_case_report(description, merged_evidence, facts)
        submission_id = f"SUB-{self._counter:04d}"
        self._counter += 1

        record = {
            "submission_id": submission_id,
            "source_case_id": source_case_id,
            "title": title or self._build_title(report["structured_data"]),
            "source": source,
            "submitted_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "description": description,
            "provided_evidence": report["structured_data"]["evidence_items"],
            "facts": facts,
            "user_profile": user_profile,
            "dispute_profile": dispute_profile,
            "evidence_catalog": evidence_catalog,
            "case_status": "已受理，待检察评估",
            "mediation_priority": "待评估",
            "prosecution_necessity": "待评估",
            "relief_checks": {
                "labor_complaint": False,
                "labor_arbitration": False,
                "legal_aid": False,
                "union_or_street_help": False,
            },
            "relief_note": "",
            "mediation_case_type": "",
            "prosecution_case_type": "",
            "prosecutor_note": "",
            "feedback_messages": [],
            "structured_data": report["structured_data"],
            "risk_assessment": report["risk_assessment"],
            "recommended_actions": report["recommended_actions"],
            "legal_basis": report["legal_basis"],
            "evidence": report["evidence"],
        }
        self._cases.append(record)
        return record

    def submit_sample_case(self, case_id: str) -> dict[str, Any]:
        sample = self.kb.get_sample_case(case_id)
        if sample is None:
            raise KeyError(case_id)
        return self.submit_case(
            description=sample["description"],
            provided_evidence=sample.get("provided_evidence", []),
            facts=sample.get("facts", {}),
            title=sample.get("title"),
            source="sample",
            source_case_id=case_id,
        )

    def dashboard(self) -> dict[str, Any]:
        items = [
            {
                "submission_id": case["submission_id"],
                "title": case["title"],
                "worker_phone": case["user_profile"].get("phone", ""),
                "employment_sector": case["dispute_profile"].get("employment_sector", "未区分"),
                "worker_name": case["structured_data"]["worker_name"],
                "employer_name": case["structured_data"]["employer_name"],
                "issue_type": case["structured_data"]["issue_type"],
                "amount_claimed": case["structured_data"]["amount_claimed"],
                "evidence_score": case["risk_assessment"]["evidence_score"],
                "risk_level": case["risk_assessment"]["level"],
                "priority_label": case["risk_assessment"]["priority_label"],
                "priority_for_prosecutor": case["risk_assessment"]["priority_for_prosecutor"],
                "case_status": case["case_status"],
                "mediation_priority": case["mediation_priority"],
                "prosecution_necessity": case["prosecution_necessity"],
                "mediation_case_type": case["mediation_case_type"],
                "prosecution_case_type": case["prosecution_case_type"],
                "submitted_at": case["submitted_at"],
                "updated_at": case["updated_at"],
                "recommended_action": case["recommended_actions"][0] if case["recommended_actions"] else "",
            }
            for case in sorted(self._cases, key=lambda item: item["submitted_at"], reverse=True)
        ]

        high_evidence_cases = [item for item in items if item["priority_for_prosecutor"]]
        return {
            "total_cases": len(items),
            "high_evidence_cases": len(high_evidence_cases),
            "items": items,
        }

    def _seed_demo_cases(self) -> None:
        for sample in self.kb.sample_cases:
            self.submit_case(
                description=sample["description"],
                provided_evidence=sample.get("provided_evidence", []),
                facts=sample.get("facts", {}),
                title=sample.get("title"),
                source="sample_seed",
                source_case_id=sample.get("case_id"),
            )

    def _build_title(self, structured_data: dict[str, Any]) -> str:
        worker_name = structured_data["worker_name"]
        issue_type = structured_data["issue_type"]
        if worker_name != "未提供":
            return f"{worker_name}{issue_type}案件"
        return f"{issue_type}案件"

    def get_case(self, submission_id: str) -> dict[str, Any]:
        for case in self._cases:
            if case["submission_id"] == submission_id:
                return case
        raise KeyError(submission_id)

    def review_case(
        self,
        submission_id: str,
        case_status: str,
        mediation_priority: str,
        prosecution_necessity: str,
        prosecutor_note: str,
        user_message: str,
        relief_checks: dict[str, bool] | None = None,
        relief_note: str = "",
        mediation_case_type: str = "",
        prosecution_case_type: str = "",
    ) -> dict[str, Any]:
        case = self.get_case(submission_id)
        case["case_status"] = case_status
        case["mediation_priority"] = mediation_priority
        case["prosecution_necessity"] = prosecution_necessity
        case["relief_checks"] = {
            "labor_complaint": bool((relief_checks or {}).get("labor_complaint")),
            "labor_arbitration": bool((relief_checks or {}).get("labor_arbitration")),
            "legal_aid": bool((relief_checks or {}).get("legal_aid")),
            "union_or_street_help": bool((relief_checks or {}).get("union_or_street_help")),
        }
        case["relief_note"] = relief_note.strip()
        case["mediation_case_type"] = mediation_case_type.strip()
        case["prosecution_case_type"] = prosecution_case_type.strip()
        case["prosecutor_note"] = prosecutor_note.strip()
        case["updated_at"] = datetime.now().isoformat(timespec="seconds")
        if user_message.strip():
            case["feedback_messages"].append(
                {
                    "sent_at": case["updated_at"],
                    "sender": "检察院端",
                    "message": user_message.strip(),
                }
            )
        return case

    def update_case_facts(self, submission_id: str, facts_patch: dict[str, Any]) -> dict[str, Any]:
        case = self.get_case(submission_id)
        merged_facts = {**case.get("facts", {}), **{k: v for k, v in facts_patch.items() if str(v).strip()}}
        case["facts"] = merged_facts
        report = self.processor.build_case_report(
            case["description"],
            case.get("provided_evidence", []),
            merged_facts,
        )
        case["structured_data"] = report["structured_data"]
        case["risk_assessment"] = report["risk_assessment"]
        case["recommended_actions"] = report["recommended_actions"]
        case["legal_basis"] = report["legal_basis"]
        case["evidence"] = report["evidence"]
        case["updated_at"] = datetime.now().isoformat(timespec="seconds")
        return case

    def _merge_evidence_catalog(
        self,
        provided_evidence: list[str] | None,
        evidence_catalog: dict[str, list[str]],
    ) -> list[str]:
        merged: list[str] = []
        for item in provided_evidence or []:
            normalized = str(item).strip()
            if normalized and normalized not in merged:
                merged.append(normalized)

        for group in evidence_catalog.values():
            for item in group:
                normalized = str(item).strip()
                if normalized and normalized not in merged:
                    merged.append(normalized)
        return merged
