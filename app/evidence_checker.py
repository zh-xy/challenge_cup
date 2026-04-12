from __future__ import annotations

from core.knowledge_base import KnowledgeBase


def evaluate_evidence(case_type: str, provided_evidence: list[str], kb: KnowledgeBase) -> dict[str, object]:
    rules = kb.get_evidence_rule(case_type)
    required = rules["required"]
    optional = rules["optional"]

    present_required = [item for item in required if item in provided_evidence]
    missing_required = [item for item in required if item not in provided_evidence]
    present_optional = [item for item in optional if item in provided_evidence]

    required_ratio = len(present_required) / len(required) if required else 0
    optional_bonus = min(0.2, len(present_optional) * 0.05)
    score = int((required_ratio + optional_bonus) * 100)
    score = min(score, 100)

    return {
        "score": score,
        "present_required": present_required,
        "missing_required": missing_required,
        "optional_evidence": optional,
        "advice": rules["advice"],
    }
