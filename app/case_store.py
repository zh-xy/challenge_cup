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
    ) -> dict[str, Any]:
        facts = facts or {}
        report = self.processor.build_case_report(description, provided_evidence, facts)
        submission_id = f"SUB-{self._counter:04d}"
        self._counter += 1

        record = {
            "submission_id": submission_id,
            "source_case_id": source_case_id,
            "title": title or self._build_title(report["structured_data"]),
            "source": source,
            "submitted_at": datetime.now().isoformat(timespec="seconds"),
            "description": description,
            "provided_evidence": report["structured_data"]["evidence_items"],
            "facts": facts,
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
                "worker_name": case["structured_data"]["worker_name"],
                "employer_name": case["structured_data"]["employer_name"],
                "issue_type": case["structured_data"]["issue_type"],
                "amount_claimed": case["structured_data"]["amount_claimed"],
                "evidence_score": case["risk_assessment"]["evidence_score"],
                "risk_level": case["risk_assessment"]["level"],
                "priority_label": case["risk_assessment"]["priority_label"],
                "priority_for_prosecutor": case["risk_assessment"]["priority_for_prosecutor"],
                "submitted_at": case["submitted_at"],
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
