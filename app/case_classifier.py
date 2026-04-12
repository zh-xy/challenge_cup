from __future__ import annotations

from collections import defaultdict


CASE_KEYWORDS = {
    "欠薪": ["欠薪", "拖欠工资", "工资没发", "工资未发", "工资", "薪资", "报酬", "欠条"],
    "工伤": ["工伤", "受伤", "骨折", "事故", "摔伤", "工伤认定", "医院", "住院", "赔偿"],
    "未签劳动合同": ["未签合同", "没签合同", "双倍工资", "劳动关系", "确认劳动关系", "入职", "用工"],
}


def classify_case(text: str) -> dict[str, object]:
    normalized = text.strip().lower()
    scores: dict[str, int] = defaultdict(int)
    matches: dict[str, list[str]] = defaultdict(list)

    for case_type, keywords in CASE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in normalized:
                scores[case_type] += 1
                matches[case_type].append(keyword)

    if not scores:
        return {
            "case_type": "欠薪",
            "confidence": 0.25,
            "matched_keywords": [],
        }

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_type, top_score = ranked[0]
    confidence = min(0.95, 0.4 + top_score * 0.12)
    return {
        "case_type": top_type,
        "confidence": round(confidence, 2),
        "matched_keywords": sorted(set(matches[top_type])),
    }
