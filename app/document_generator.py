from __future__ import annotations

from datetime import date
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.knowledge_base import TEMPLATE_DIR


class DocumentGenerator:
    TEMPLATE_MAP = {
        "arbitration_application": "arbitration_application.j2",
        "support_prosecution_application": "support_prosecution_application.j2",
    }

    def __init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(
        self,
        template_name: str,
        case_report: dict[str, Any],
        facts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if template_name not in self.TEMPLATE_MAP:
            raise ValueError(f"Unsupported template: {template_name}")

        facts = facts or {}
        structured = case_report["structured_data"]
        assessment = case_report["risk_assessment"]
        evidence = case_report["evidence"]
        template = self.env.get_template(self.TEMPLATE_MAP[template_name])

        context = {
            "today": date.today().isoformat(),
            "worker_name": facts.get("worker_name") or structured["worker_name"],
            "company_name": facts.get("company_name") or structured["employer_name"],
            "amount": facts.get("amount") or structured["amount_claimed"] or "待核定",
            "job_title": facts.get("job_title", "务工人员"),
            "start_date": facts.get("start_date", "待补充"),
            "end_date": facts.get("end_date", "待补充"),
            "dispute_type": structured["issue_type"],
            "dispute_summary": structured["raw_text"],
            "evidence_list": structured["evidence_items"] or ["待补充"],
            "risk_level": assessment["level"],
            "evidence_score": assessment["evidence_score"],
            "recommended_actions": case_report["recommended_actions"],
            "missing_evidence": evidence["missing_required"],
        }

        return {
            "document_type": template_name,
            "document_text": template.render(**context),
            "context": context,
        }
