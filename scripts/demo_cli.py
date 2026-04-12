from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.service import generate_document, get_prosecutor_dashboard, kb, submit_sample_case


def main() -> None:
    sample = kb.get_sample_case("A001")
    if sample is None:
        raise SystemExit("Sample case not found")

    submission = submit_sample_case("A001")
    document = generate_document(
        "arbitration_application",
        sample["description"],
        sample["facts"],
        sample["provided_evidence"],
    )

    print("=== SUBMISSION ===")
    print(json.dumps(submission, ensure_ascii=False, indent=2))
    print("=== DOCUMENT ===")
    print(document["document_text"])
    print("=== DASHBOARD ===")
    print(json.dumps(get_prosecutor_dashboard(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
