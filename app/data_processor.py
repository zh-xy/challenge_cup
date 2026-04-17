from __future__ import annotations

from typing import Any

from app.case_analysis import ActionPlanner, EvidenceAnalyzer, RiskScorer, TextExtractor
from core.knowledge_base import KnowledgeBase
from core.models import CaseReport


class DataProcessor:
    def __init__(
        self,
        kb: KnowledgeBase,
        extractor: TextExtractor | None = None,
        evidence_analyzer: EvidenceAnalyzer | None = None,
        risk_scorer: RiskScorer | None = None,
        action_planner: ActionPlanner | None = None,
    ) -> None:
        self.kb = kb
        self.extractor = extractor or TextExtractor()
        self.evidence_analyzer = evidence_analyzer or EvidenceAnalyzer(kb)
        self.risk_scorer = risk_scorer or RiskScorer()
        self.action_planner = action_planner or ActionPlanner()

    def build_case_report(
        self,
        raw_text: str,
        provided_evidence: list[str] | None = None,
        facts: dict[str, Any] | None = None,
    ) -> CaseReport:
        structured = self.extractor.extract(raw_text, provided_evidence, facts)
        evidence_summary, evidence_score = self.evidence_analyzer.summarize(structured)
        risk_assessment = self.risk_scorer.score(structured, evidence_summary, evidence_score)
        recommended_actions = self.action_planner.build(structured, evidence_summary, evidence_score)
        legal_basis = self.kb.get_laws_for_scene(structured.issue_type)
        return CaseReport(
            structured_data=structured,
            risk_assessment=risk_assessment,
            recommended_actions=recommended_actions,
            legal_basis=legal_basis,
            evidence=evidence_summary,
        )
