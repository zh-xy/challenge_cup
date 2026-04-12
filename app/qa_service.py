from __future__ import annotations

import json

from app.llm_client import LLMClient
from core.knowledge_base import KnowledgeBase


def _build_fallback_answer(question: str, kb: KnowledgeBase) -> dict[str, object]:
    normalized = question.strip().lower()
    best_item = None
    best_score = 0

    for item in kb.faq:
        score = 0
        for trigger in item["triggers"]:
            if trigger.lower() in normalized:
                score += len(trigger)
        if score > best_score:
            best_score = score
            best_item = item

    if best_item is None:
        return {
            "question_type": "通用咨询",
            "scene": "欠薪",
            "summary": "当前版本仅覆盖欠薪、工伤、未签劳动合同等高频劳动争议场景，建议改用更具体的提问方式。",
            "steps": [
                "明确争议类型，例如欠薪、工伤、未签劳动合同",
                "补充是否有合同、工资流水、病历、聊天记录等证据",
            ],
            "materials": ["案情描述", "已有证据材料"],
            "risk_tip": "超出演示场景的问题目前无法稳定回答。",
            "legal_basis": [],
        }

    laws = kb.get_laws_for_scene(best_item["scene"])
    return {
        "question_type": best_item["question_type"],
        "scene": best_item["scene"],
        "summary": best_item["answer"]["summary"],
        "steps": best_item["answer"]["steps"],
        "materials": best_item["answer"]["materials"],
        "risk_tip": best_item["answer"]["risk_tip"],
        "legal_basis": [{"title": law["title"], "summary": law["summary"]} for law in laws],
    }


def _build_system_prompt(kb: KnowledgeBase) -> str:
    faq_context = []
    for item in kb.faq:
        faq_context.append(
            {
                "question_type": item["question_type"],
                "scene": item["scene"],
                "triggers": item["triggers"],
                "answer": item["answer"],
                "legal_basis": [
                    {"title": law["title"], "summary": law["summary"]}
                    for law in kb.get_laws_for_scene(item["scene"])
                ],
            }
        )

    return (
        "你是农民工权益保障智能平台的法律辅助问答模块。"
        "你只能基于给定知识库回答，场景仅限欠薪、工伤、未签劳动合同。"
        "如果用户问题超出范围，也要返回谨慎、收敛的回答，不得编造法条、流程或结论。"
        "输出必须是 JSON 对象，字段固定为："
        "question_type, scene, summary, steps, materials, risk_tip, legal_basis。"
        "其中 steps/materials/legal_basis 必须是数组，legal_basis 数组元素必须包含 title 和 summary。"
        "如果无法稳定判断，question_type 写“通用咨询”，scene 写最接近场景或“欠薪”，"
        "summary 里明确说明当前系统覆盖范围有限。"
        "以下是知识库："
        f"{json.dumps(faq_context, ensure_ascii=False)}"
    )


def _build_user_prompt(question: str) -> str:
    return (
        "请根据知识库回答下面的问题，并严格输出 JSON 对象，不要输出 Markdown。\n"
        f"用户问题：{question}"
    )


def _normalize_llm_answer(answer: dict[str, object], kb: KnowledgeBase) -> dict[str, object]:
    scene = str(answer.get("scene") or "欠薪")
    if scene not in {"欠薪", "工伤", "未签劳动合同"}:
        scene = "欠薪"

    question_type = str(answer.get("question_type") or "通用咨询")
    summary = str(answer.get("summary") or "当前未能生成稳定回答，请尝试描述争议类型和已有证据。")
    risk_tip = str(answer.get("risk_tip") or "请结合证据情况进一步核实。")

    steps = answer.get("steps")
    if not isinstance(steps, list) or not all(isinstance(item, str) for item in steps):
        steps = [
            "明确争议类型和关键事实",
            "整理劳动关系、工资、医疗或沟通记录等材料",
            "必要时向劳动仲裁或相关部门进一步咨询",
        ]

    materials = answer.get("materials")
    if not isinstance(materials, list) or not all(isinstance(item, str) for item in materials):
        materials = ["案情描述", "已有证据材料"]

    legal_basis = answer.get("legal_basis")
    if not isinstance(legal_basis, list):
        legal_basis = []

    normalized_laws: list[dict[str, str]] = []
    for item in legal_basis:
        if isinstance(item, dict) and item.get("title") and item.get("summary"):
            normalized_laws.append(
                {
                    "title": str(item["title"]),
                    "summary": str(item["summary"]),
                }
            )
    if not normalized_laws:
        normalized_laws = [
            {"title": law["title"], "summary": law["summary"]}
            for law in kb.get_laws_for_scene(scene)
        ]

    return {
        "question_type": question_type,
        "scene": scene,
        "summary": summary,
        "steps": steps,
        "materials": materials,
        "risk_tip": risk_tip,
        "legal_basis": normalized_laws,
    }


def answer_question(question: str, kb: KnowledgeBase, llm_client: LLMClient | None = None) -> dict[str, object]:
    client = llm_client or LLMClient()
    fallback = _build_fallback_answer(question, kb)

    if not client.enabled:
        return {
            **fallback,
            "answer_source": "rule_fallback",
        }

    try:
        llm_answer = client.chat_json(
            system_prompt=_build_system_prompt(kb),
            user_prompt=_build_user_prompt(question),
        )
        return {
            **_normalize_llm_answer(llm_answer, kb),
            "answer_source": "dashscope_llm",
            "llm_model": client.model,
        }
    except Exception as exc:
        return {
            **fallback,
            "answer_source": "rule_fallback",
            "fallback_reason": f"LLM unavailable: {exc}",
        }
