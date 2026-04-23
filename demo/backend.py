from __future__ import annotations

import json
from typing import Any

import streamlit as st

from demo.api_client import ApiClient
from demo.config import DEFAULT_API_BASE_URL, PROJECT_ROOT


def get_api_client() -> ApiClient:
    return ApiClient(st.session_state.get("api_base_url", DEFAULT_API_BASE_URL))


def safe_get(path: str, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        return get_api_client().get(path)
    except RuntimeError as exc:
        st.warning(f"后端接口暂不可用：{exc}")
        return fallback or {}


def safe_post(path: str, payload: dict[str, Any], fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        return get_api_client().post(path, payload)
    except RuntimeError as exc:
        st.error(f"后端接口调用失败：{exc}")
        return fallback or {}


def get_sample_cases() -> list[dict[str, Any]]:
    sample_cases = safe_get("/cases/samples", {"items": []}).get("items", [])
    if sample_cases:
        return sample_cases

    sample_path = PROJECT_ROOT / "data" / "sample_cases.json"
    try:
        with sample_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return []
    return payload if isinstance(payload, list) else []


def ask_legal_question(question: str) -> dict[str, Any]:
    return safe_post("/qa/answer", {"question": question})


def build_analysis(description: str, evidence_items: list[str], facts: dict[str, Any]) -> dict[str, Any]:
    return safe_post(
        "/case/analyze",
        {
            "description": description,
            "provided_evidence": evidence_items,
            "facts": facts,
        },
    )


def build_document(case_report: dict[str, Any], template_name: str, facts: dict[str, Any]) -> dict[str, Any]:
    return safe_post(
        "/document/generate",
        {
            "template_name": template_name,
            "description": case_report["structured_data"]["raw_text"],
            "provided_evidence": case_report["structured_data"]["evidence_items"],
            "facts": facts,
        },
    )


def build_route_recommendations(
    analysis_report: dict[str, Any],
    last_submission: dict[str, Any] | None,
) -> list[dict[str, str]]:
    assessment = analysis_report["risk_assessment"]
    structured = analysis_report["structured_data"]
    routes: list[dict[str, str]] = []

    if last_submission and last_submission.get("case_status") == "建议优先调解":
        routes.append(
            {
                "title": "优先调解",
                "copy": "检察院端已标记为可优先调解，适合先通过协商或行政协调降低维权成本。",
            }
        )

    if assessment["evidence_score"] >= 75:
        routes.append(
            {
                "title": "申请支持起诉",
                "copy": "当前证据分数较高，适合进入支持起诉或文书生成流程，由检察院端进一步研判。",
            }
        )
    else:
        routes.append(
            {
                "title": "先补充证据",
                "copy": "现阶段建议优先补齐劳动关系、工资约定、考勤或聊天记录，再进入起诉或支持起诉流程。",
            }
        )

    if structured["issue_type"] in {"欠薪", "未签劳动合同"}:
        routes.append(
            {
                "title": "劳动监察 / 劳动仲裁",
                "copy": "若争议集中在拖欠工资、双倍工资或劳动关系确认，可优先走劳动监察投诉或劳动仲裁。",
            }
        )
    else:
        routes.append(
            {
                "title": "行政认定 + 后续救济",
                "copy": "工伤类争议建议优先补齐诊断材料、事故说明和工伤认定材料，再同步准备后续索赔。",
            }
        )

    routes.append(
        {
            "title": "法律援助 / 文书辅助",
            "copy": "如自行起诉能力不足，可先使用平台文书生成能力，并同步寻求法律援助。",
        }
    )
    return routes


def build_case_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered_cases = sorted(cases, key=lambda item: item["submitted_at"], reverse=True)
    rows: list[dict[str, Any]] = []
    for case in ordered_cases:
        rows.append(
            {
                "提交编号": case["submission_id"],
                "案件标题": case["title"],
                "劳动者": case["worker_name"],
                "联系电话": case["worker_phone"] or "未填",
                "用工主体": case["employer_name"],
                "领域": case["employment_sector"],
                "纠纷类型": case["issue_type"],
                "涉案金额(元)": case["amount_claimed"] or 0,
                "证据分数": case["evidence_score"],
                "风险等级": case["risk_level"],
                "优先级": case["priority_label"],
                "案件状态": case["case_status"],
                "建议动作": case["recommended_action"],
                "提交时间": case["submitted_at"],
            }
        )
    return rows


def build_evidence_advice(case_detail: dict[str, Any]) -> list[dict[str, str]]:
    advice: list[dict[str, str]] = []
    for item in case_detail.get("evidence", {}).get("missing_required", []):
        advice.append(
            {
                "material": item,
                "reason": "属于当前纠纷类型下的关键缺失证据，建议优先补齐或由检察院协助调取。",
            }
        )

    standard_materials = [
        ("劳动合同", "可直接证明劳动关系、岗位与工资约定。"),
        ("职工名册", "可证明实名制用工和劳动关系存续情况。"),
        ("支付台账", "可核对工资支付周期、应发实发差额和欠薪时间。"),
        ("工资清单", "可辅助固定工资标准、支付方式和欠薪金额。"),
    ]
    for material, reason in standard_materials:
        advice.append({"material": material, "reason": reason})
    return advice
