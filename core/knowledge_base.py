from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = DATA_DIR / "templates"


def load_json(name: str) -> Any:
    path = DATA_DIR / name
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


class KnowledgeBase:
    def __init__(self) -> None:
        self.laws = load_json("laws.json")
        self.evidence_rules = load_json("evidence_rules.json")
        self.faq = load_json("faq.json")
        self.sample_cases = load_json("sample_cases.json")

    def get_laws_for_scene(self, scene: str) -> list[dict[str, str]]:
        return [law for law in self.laws if law["scene"] == scene]

    def get_evidence_rule(self, scene: str) -> dict[str, list[str]]:
        return self.evidence_rules.get(scene, {"required": [], "optional": [], "advice": []})

    def get_sample_case(self, case_id: str) -> dict[str, Any] | None:
        for case in self.sample_cases:
            if case["case_id"] == case_id:
                return case
        return None
