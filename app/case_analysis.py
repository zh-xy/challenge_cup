from __future__ import annotations

import re
from typing import Any

from core.knowledge_base import KnowledgeBase
from core.models import EvidenceSummary, RiskAssessment, StructuredCaseData


CASE_KEYWORDS = {
    "欠薪": ["欠薪", "拖欠工资", "工资没发", "工资未发", "工资", "薪资", "报酬", "结算"],
    "工伤": ["工伤", "受伤", "骨折", "摔伤", "砸伤", "事故", "住院", "治疗", "赔偿"],
    "未签劳动合同": ["未签合同", "没签合同", "没有合同", "双倍工资", "劳动关系", "确认劳动关系"],
}

EVIDENCE_HINTS = {
    "身份证明": ["身份证"],
    "劳动合同或用工证明": ["劳动合同", "合同", "用工证明", "工牌", "工作证"],
    "工资约定证明": ["工资标准", "工资约定", "口头约定", "单价"],
    "考勤记录或工作记录": ["考勤", "打卡", "工作记录", "施工记录"],
    "工资流水或欠薪记录": ["工资流水", "银行流水", "转账记录", "欠条", "欠薪记录"],
    "聊天记录": ["微信", "聊天记录", "语音记录"],
    "工友证言": ["工友证言", "同事证明", "证人"],
    "工作照片": ["工作照片", "现场照片", "工地照片"],
    "事故经过说明": ["事故说明", "事故经过"],
    "医院诊断材料": ["诊断证明", "住院", "病历", "医院材料", "诊断"],
    "工伤认定材料": ["工伤认定", "认定申请"],
    "医疗费票据": ["票据", "发票", "医疗费"],
    "入职时间证明": ["入职", "到岗", "上班时间"],
    "实际工作证明": ["工作群", "工作安排", "岗位", "干活"],
    "工资支付记录": ["发工资", "微信转账", "工资支付", "工资流水"],
    "未签合同情况说明": ["未签合同", "没签合同", "没有合同"],
    "工牌照片": ["工牌"],
    "招聘记录": ["招聘", "招工"],
}

CHINESE_NUMERALS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


class TextExtractor:
    def extract(
        self,
        raw_text: str,
        provided_evidence: list[str] | None = None,
        facts: dict[str, Any] | None = None,
    ) -> StructuredCaseData:
        text = raw_text.strip()
        facts = facts or {}
        evidence_items = self._merge_evidence(provided_evidence or [], text)
        worker_name = self._extract_worker_name(text, facts)
        employer_name = self._extract_employer_name(text, facts)
        issue_type = self._detect_issue_type(text)
        amount_claimed = self._extract_amount(text, facts)
        unpaid_duration = self._extract_duration_months(text, facts)
        has_contract = self._extract_contract_status(text, facts)
        injury_occurred = issue_type == "工伤" or any(keyword in text for keyword in ["受伤", "骨折", "住院", "摔伤"])
        notes: list[str] = []

        if worker_name == "未提供":
            notes.append("未从文本中识别到劳动者姓名，已使用默认值。")
        if employer_name == "未提供":
            notes.append("未从文本中识别到用工主体，建议补充公司或包工头名称。")
        if amount_claimed is None:
            notes.append("未识别到明确金额，建议补充欠薪或赔偿金额。")
        if unpaid_duration is None and issue_type == "欠薪":
            notes.append("未识别到欠薪时长，建议补充拖欠月份。")

        return StructuredCaseData(
            worker_name=worker_name,
            employer_name=employer_name,
            issue_type=issue_type,
            amount_claimed=amount_claimed,
            unpaid_duration_months=unpaid_duration,
            has_contract=has_contract,
            injury_occurred=injury_occurred,
            raw_text=text,
            evidence_items=evidence_items,
            facts=facts,
            extraction_notes=notes,
        )

    def _merge_evidence(self, provided_evidence: list[str], raw_text: str) -> list[str]:
        evidence_items = list(dict.fromkeys(item.strip() for item in provided_evidence if item.strip()))
        normalized = raw_text.strip()
        for canonical, hints in EVIDENCE_HINTS.items():
            if canonical in evidence_items:
                continue
            if any(hint in normalized for hint in hints):
                evidence_items.append(canonical)
        return evidence_items

    def _detect_issue_type(self, text: str) -> str:
        ranked = [
            (issue_type, sum(1 for keyword in keywords if keyword in text))
            for issue_type, keywords in CASE_KEYWORDS.items()
        ]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[0][0] if ranked and ranked[0][1] > 0 else "欠薪"

    def _extract_worker_name(self, text: str, facts: dict[str, Any]) -> str:
        if facts.get("worker_name"):
            return str(facts["worker_name"])

        patterns = [
            r"(?:我叫|本人叫)([\u4e00-\u9fa5]{2,4})",
            r"([\u4e00-\u9fa5]{1,3}某)",
            r"([\u4e00-\u9fa5]{2,4})(?:在|于|是)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return "未提供"

    def _extract_employer_name(self, text: str, facts: dict[str, Any]) -> str:
        company_name = facts.get("company_name") or facts.get("employer_name")
        if company_name:
            return str(company_name)

        patterns = [
            r"在([\u4e00-\u9fa5A-Za-z0-9]{2,30}(?:公司|工厂|工地|项目部|劳务队))",
            r"([\u4e00-\u9fa5A-Za-z0-9]{2,30}(?:公司|工厂|工地|项目部|劳务队))",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return "未提供"

    def _extract_amount(self, text: str, facts: dict[str, Any]) -> int | None:
        fact_amount = facts.get("amount") or facts.get("amount_claimed")
        if fact_amount not in (None, ""):
            try:
                return int(str(fact_amount))
            except ValueError:
                pass

        match = re.search(r"(\d+(?:\.\d+)?)\s*万", text)
        if match:
            return int(float(match.group(1)) * 10000)

        match = re.search(r"(\d+(?:\.\d+)?)\s*元", text)
        if match:
            return int(float(match.group(1)))

        chinese_match = re.search(r"([一二两三四五六七八九十]+)\s*万", text)
        if chinese_match:
            return self._parse_chinese_number(chinese_match.group(1)) * 10000
        return None

    def _extract_duration_months(self, text: str, facts: dict[str, Any]) -> int | None:
        fact_duration = facts.get("unpaid_duration_months") or facts.get("duration_months")
        if fact_duration not in (None, ""):
            try:
                return int(str(fact_duration))
            except ValueError:
                pass

        match = re.search(r"(\d+)\s*个?月", text)
        if match:
            return int(match.group(1))

        chinese_match = re.search(r"([一二两三四五六七八九十]+)\s*个?月", text)
        if chinese_match:
            return self._parse_chinese_number(chinese_match.group(1))
        return None

    def _extract_contract_status(self, text: str, facts: dict[str, Any]) -> bool | None:
        if "has_contract" in facts and facts["has_contract"] is not None:
            return bool(facts["has_contract"])

        negative_keywords = ["没签合同", "未签合同", "没有合同", "未订立劳动合同"]
        positive_keywords = ["签了合同", "签订合同", "劳动合同"]

        if any(keyword in text for keyword in negative_keywords):
            return False
        if any(keyword in text for keyword in positive_keywords):
            return True
        return None

    def _parse_chinese_number(self, text: str) -> int:
        if not text:
            return 0
        if text == "十":
            return 10
        if "十" in text:
            left, _, right = text.partition("十")
            tens = CHINESE_NUMERALS.get(left, 1) if left else 1
            ones = CHINESE_NUMERALS.get(right, 0) if right else 0
            return tens * 10 + ones
        return CHINESE_NUMERALS.get(text, 0)


class EvidenceAnalyzer:
    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb

    def summarize(self, structured_data: StructuredCaseData) -> tuple[EvidenceSummary, int]:
        rules = self.kb.get_evidence_rule(structured_data.issue_type)
        required = rules["required"]
        optional = rules["optional"]
        evidence_items = structured_data.evidence_items

        present_required = [item for item in required if item in evidence_items]
        missing_required = [item for item in required if item not in evidence_items]
        present_optional = [item for item in optional if item in evidence_items]

        fact_completeness = 0
        if structured_data.worker_name != "未提供":
            fact_completeness += 1
        if structured_data.employer_name != "未提供":
            fact_completeness += 1
        if structured_data.amount_claimed is not None:
            fact_completeness += 1
        if structured_data.unpaid_duration_months is not None:
            fact_completeness += 1

        required_ratio = len(present_required) / len(required) if required else 0
        optional_ratio = len(present_optional) / len(optional) if optional else 0
        fact_ratio = fact_completeness / 4
        evidence_score = round(min(100, required_ratio * 70 + optional_ratio * 15 + fact_ratio * 15))

        return (
            EvidenceSummary(
                present_required=present_required,
                missing_required=missing_required,
                optional_evidence=optional,
            ),
            evidence_score,
        )


class RiskScorer:
    def score(self, structured_data: StructuredCaseData, evidence_summary: EvidenceSummary, evidence_score: int) -> RiskAssessment:
        risk_score = 55
        issue_type = structured_data.issue_type

        if issue_type == "欠薪":
            if (structured_data.unpaid_duration_months or 0) >= 3:
                risk_score += 18
            if structured_data.has_contract is False:
                risk_score += 12
        elif issue_type == "工伤":
            if "工伤认定材料" in evidence_summary.missing_required:
                risk_score += 20
            if structured_data.has_contract is False:
                risk_score += 8
        elif issue_type == "未签劳动合同":
            if structured_data.has_contract is False:
                risk_score += 16
            if (structured_data.unpaid_duration_months or 0) >= 6:
                risk_score += 8

        risk_score += min(20, len(evidence_summary.missing_required) * 5)
        risk_score -= round(evidence_score * 0.45)
        risk_score = max(5, min(100, risk_score))

        if risk_score >= 70:
            risk_level = "高风险"
        elif risk_score >= 45:
            risk_level = "中风险"
        else:
            risk_level = "低风险"

        reasons = [f"当前识别的纠纷类型为“{issue_type}”，证据分数为 {evidence_score} 分。"]
        if issue_type == "欠薪" and (structured_data.unpaid_duration_months or 0) >= 3:
            reasons.append("欠薪时长达到 3 个月及以上，属于需要尽快介入的情形。")
        if structured_data.has_contract is False:
            reasons.append("文本显示未签劳动合同，劳动关系与用工主体证明难度会增加。")
        if evidence_summary.missing_required:
            reasons.append(
                f"仍缺少 {len(evidence_summary.missing_required)} 项关键证据：{'、'.join(evidence_summary.missing_required)}。"
            )
        else:
            reasons.append("当前必备证据已基本齐备，可直接进入程序性维权阶段。")
        reasons.append(f"综合规则引擎判定该案为{risk_level}。")

        priority_for_prosecutor = evidence_score >= 75
        priority_label = "高证据优先关注" if priority_for_prosecutor else "常规跟进"
        return RiskAssessment(
            level=risk_level,
            score=risk_score,
            evidence_score=evidence_score,
            priority_for_prosecutor=priority_for_prosecutor,
            priority_label=priority_label,
            reasons=reasons,
        )


class ActionPlanner:
    def build(self, structured_data: StructuredCaseData, evidence_summary: EvidenceSummary, evidence_score: int) -> list[str]:
        issue_type = structured_data.issue_type
        actions: list[str] = []

        if issue_type == "欠薪":
            actions.extend(
                [
                    "优先整理工资标准、欠薪月份和实际工作天数，形成时间轴。",
                    "先申请劳动仲裁；如存在批量欠薪或执行困难，可同步准备检察支持起诉材料。",
                ]
            )
        elif issue_type == "工伤":
            actions.extend(
                [
                    "先补齐工伤认定申请材料，再主张工伤待遇或赔偿。",
                    "固定事故时间、地点、岗位和就医资料，避免事实链断裂。",
                ]
            )
        else:
            actions.extend(
                [
                    "重点固定入职时间、持续用工事实和工资支付记录。",
                    "可先通过劳动仲裁确认劳动关系，再主张双倍工资。",
                ]
            )

        if evidence_summary.missing_required:
            actions.append(f"优先补齐：{'、'.join(evidence_summary.missing_required)}。")
        if evidence_score >= 75:
            actions.append("证据基础较强，建议纳入检察院优先研判清单。")
        return actions
