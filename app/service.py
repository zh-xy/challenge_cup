from __future__ import annotations

from typing import Any

from app.case_store import CaseStore
from app.data_processor import DataProcessor
from app.document_generator import DocumentGenerator
from app.llm_client import LLMClient
from app.qa_service import answer_question
from core.knowledge_base import KnowledgeBase


kb = KnowledgeBase()
data_processor = DataProcessor(kb)
document_generator = DocumentGenerator()
case_store = CaseStore(kb, data_processor)
llm_client = LLMClient()


def analyze_case(
    description: str,
    provided_evidence: list[str] | None = None,
    facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return data_processor.build_case_report(description, provided_evidence, facts)


def submit_case(
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
    return case_store.submit_case(
        description,
        provided_evidence,
        facts,
        title,
        source,
        source_case_id,
        user_profile,
        dispute_profile,
        evidence_catalog,
    )


def submit_sample_case(case_id: str) -> dict[str, Any]:
    return case_store.submit_sample_case(case_id)


def list_sample_cases() -> list[dict[str, Any]]:
    return kb.sample_cases


def list_submitted_cases() -> list[dict[str, Any]]:
    return case_store.list_submissions()


def get_case_detail(submission_id: str) -> dict[str, Any]:
    return case_store.get_case(submission_id)


def get_prosecutor_dashboard() -> dict[str, Any]:
    return case_store.dashboard()


def review_case(
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
    return case_store.review_case(
        submission_id=submission_id,
        case_status=case_status,
        mediation_priority=mediation_priority,
        prosecution_necessity=prosecution_necessity,
        prosecutor_note=prosecutor_note,
        user_message=user_message,
        relief_checks=relief_checks,
        relief_note=relief_note,
        mediation_case_type=mediation_case_type,
        prosecution_case_type=prosecution_case_type,
    )


def update_case_facts(
    submission_id: str,
    facts_patch: dict[str, Any],
) -> dict[str, Any]:
    return case_store.update_case_facts(submission_id, facts_patch)


def generate_document(
    template_name: str,
    description: str,
    facts: dict[str, Any] | None = None,
    provided_evidence: list[str] | None = None,
) -> dict[str, Any]:
    case_report = analyze_case(description, provided_evidence, facts)
    return document_generator.generate(template_name, case_report, facts)


def ask_question(question: str) -> dict[str, object]:
    return answer_question(question, kb, llm_client)
