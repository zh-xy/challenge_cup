from __future__ import annotations


def make_decision(case_type: str, evidence_score: int, missing_evidence: list[str]) -> dict[str, object]:
    reasoning: list[str] = []
    follow_up_steps: list[str] = []

    if case_type == "欠薪":
        recommended_action = "建议先申请劳动仲裁，再视结果申请强制执行或提起诉讼。"
        follow_up_steps = [
            "明确拖欠工资的月份、金额和工资标准",
            "补充工资流水、考勤记录等关键证据",
            "向劳动人事争议仲裁委员会提交申请"
        ]
    elif case_type == "工伤":
        recommended_action = "建议先推进工伤认定，再根据认定结果主张工伤待遇或赔偿。"
        follow_up_steps = [
            "核实是否已提交工伤认定申请",
            "补齐诊断证明、病历和事故经过材料",
            "后续再评估赔偿项目和诉求金额"
        ]
    else:
        recommended_action = "建议先确认劳动关系并申请劳动仲裁，必要时主张未签劳动合同双倍工资。"
        follow_up_steps = [
            "固定入职时间和持续用工事实",
            "整理工资支付记录和工作聊天记录",
            "先通过仲裁确认权利基础"
        ]

    if evidence_score >= 80:
        risk_level = "低"
        reasoning.append("关键证据较完整，具备较强维权基础。")
    elif evidence_score >= 55:
        risk_level = "中"
        reasoning.append("已有部分关键证据，但仍需补强关键事实。")
    else:
        risk_level = "高"
        reasoning.append("关键证据缺口较大，直接主张权利的风险较高。")

    if missing_evidence:
        reasoning.append(f"当前仍缺少 {len(missing_evidence)} 项必备证据，应优先补齐。")
    else:
        reasoning.append("当前未发现必备证据缺项。")

    return {
        "risk_level": risk_level,
        "recommended_action": recommended_action,
        "reasoning": reasoning,
        "follow_up_steps": follow_up_steps,
    }
