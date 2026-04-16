from __future__ import annotations

from datetime import date
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.knowledge_base import TEMPLATE_DIR


class DocumentGenerator:
    TEMPLATE_MAP = {
        "arbitration_application": "arbitration_application.j2",
        "support_prosecution_application": "support_prosecution_application.j2",
        "civil_complaint_non_construction": "civil_complaint_non_construction.j2",
        "civil_complaint_construction": "civil_complaint_construction.j2",
        "support_prosecution_opinion_non_construction": "support_prosecution_opinion_non_construction.j2",
        "support_prosecution_opinion_construction": "support_prosecution_opinion_construction.j2",
    }
    TEMPLATE_REQUIREMENTS = {
        "arbitration_application": [
            ("worker_name", "申请人姓名", "农民工端填写"),
            ("company_name", "被申请人名称", "农民工端填写 / 企业信息检索"),
            ("amount", "争议金额", "农民工端填写"),
            ("job_title", "工种/岗位", "农民工端填写"),
            ("start_date", "工作开始时间", "农民工端填写"),
            ("end_date", "工作结束时间", "农民工端填写"),
        ],
        "support_prosecution_application": [
            ("worker_name", "申请人姓名", "农民工端填写"),
            ("company_name", "被申请支持对象", "农民工端填写 / 企业信息检索"),
            ("amount", "争议金额", "农民工端填写"),
            ("evidence_list", "已掌握证据", "农民工端提交"),
        ],
        "civil_complaint_non_construction": [
            ("worker_name", "原告姓名", "农民工端填写"),
            ("worker_gender", "原告性别", "农民工端填写 / 身份证信息"),
            ("worker_birth_date", "原告出生日期", "农民工端填写 / 身份证信息"),
            ("worker_ethnicity", "原告民族", "农民工端填写 / 身份证信息"),
            ("worker_id_number", "原告身份证号", "农民工端填写 / 身份证信息"),
            ("worker_address", "原告住址", "农民工端填写"),
            ("worker_phone", "原告联系电话", "农民工端填写"),
            ("company_name", "被告单位名称", "农民工端填写 / 企业信息检索"),
            ("company_credit_code", "被告统一社会信用代码", "企业信用信息检索"),
            ("company_address", "被告住所地", "企业信用信息检索"),
            ("company_legal_rep", "被告法定代表人", "企业信用信息检索"),
            ("company_phone", "被告联系电话", "企业信用信息检索 / 当事人提供"),
            ("direct_employer_name", "直接雇佣人姓名", "农民工端填写 / 检察院核实"),
            ("direct_employer_id_number", "直接雇佣人身份证号", "检察院调取 / 当事人补充"),
            ("claim_amount", "诉请金额", "农民工端填写 / 工资台账核算"),
            ("work_start_date", "工作起始时间", "农民工端填写"),
            ("work_unit_name", "工作单位", "农民工端填写"),
            ("employment_days", "工作天数", "考勤记录 / 农民工补充"),
            ("wage_rate", "工资标准", "聊天记录 / 工资单 / 招工记录"),
            ("court_name", "管辖法院", "根据工作地或住所地确定"),
        ],
        "civil_complaint_construction": [
            ("worker_name", "原告姓名", "农民工端填写"),
            ("worker_id_number", "原告身份证号", "农民工端填写 / 身份证信息"),
            ("worker_address", "原告住址", "农民工端填写"),
            ("worker_phone", "原告联系电话", "农民工端填写"),
            ("contractor_name", "总包单位", "住建信息检索 / 检察院核实"),
            ("contractor_credit_code", "总包统一社会信用代码", "住建/企业信息检索"),
            ("subcontractor_name", "分包单位", "住建信息检索 / 检察院核实"),
            ("subcontractor_credit_code", "分包统一社会信用代码", "住建/企业信息检索"),
            ("guarantor_name", "担保方", "工程合同 / 检察院核实"),
            ("direct_employer_name", "直接雇佣人", "农民工端填写 / 检察院核实"),
            ("project_name", "工作项目", "农民工端填写 / 住建信息检索"),
            ("claim_amount", "诉请金额", "农民工端填写 / 工资台账核算"),
            ("employment_days", "工作天数", "考勤记录 / 施工记录"),
            ("wage_rate", "工资标准", "聊天记录 / 结算单 / 工资单"),
            ("court_name", "管辖法院", "根据工作地或住所地确定"),
        ],
        "support_prosecution_opinion_non_construction": [
            ("procuratorate_name", "检察院名称", "检察院端填写"),
            ("worker_name", "劳动者姓名", "农民工端填写"),
            ("direct_employer_name", "直接雇佣人", "农民工端填写 / 检察院核实"),
            ("company_name", "工作单位", "农民工端填写 / 企业信息检索"),
            ("claim_amount", "诉请金额", "工资台账 / 农民工主张"),
            ("court_name", "受理法院", "根据工作地或住所地确定"),
        ],
        "support_prosecution_opinion_construction": [
            ("procuratorate_name", "检察院名称", "检察院端填写"),
            ("worker_name", "劳动者姓名", "农民工端填写"),
            ("project_name", "工程项目名称", "农民工端填写 / 住建信息检索"),
            ("contractor_name", "总包单位", "住建信息检索"),
            ("subcontractor_name", "分包单位", "住建信息检索"),
            ("guarantor_name", "担保方", "工程合同 / 检察院核实"),
            ("direct_employer_name", "直接雇佣人", "农民工端填写 / 检察院核实"),
            ("claim_amount", "诉请金额", "工资台账 / 农民工主张"),
            ("court_name", "受理法院", "根据工作地或住所地确定"),
        ],
    }

    def __init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(
        self,
        template_name: str,
        case_report: dict[str, Any],
        facts: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if template_name not in self.TEMPLATE_MAP:
            raise ValueError(f"Unsupported template: {template_name}")

        facts = facts or {}
        structured = case_report["structured_data"]
        assessment = case_report["risk_assessment"]
        evidence = case_report["evidence"]
        template = self.env.get_template(self.TEMPLATE_MAP[template_name])
        amount = facts.get("amount") or structured["amount_claimed"] or "待核定"

        context = {
            "today": date.today().isoformat(),
            "worker_name": facts.get("worker_name") or structured["worker_name"],
            "worker_gender": facts.get("worker_gender", "性别待补充"),
            "worker_birth_date": facts.get("worker_birth_date", "出生日期待补充"),
            "worker_ethnicity": facts.get("worker_ethnicity", "民族待补充"),
            "worker_id_number": facts.get("worker_id_number", "身份证号待补充"),
            "worker_address": facts.get("worker_address", "住址待补充"),
            "worker_phone": facts.get("worker_phone", "联系电话待补充"),
            "company_name": facts.get("company_name") or structured["employer_name"],
            "company_credit_code": facts.get("company_credit_code", "统一社会信用代码待补充"),
            "company_address": facts.get("company_address", "住所地待补充"),
            "company_legal_rep": facts.get("company_legal_rep", "法定代表人待补充"),
            "company_phone": facts.get("company_phone", "联系电话待补充"),
            "direct_employer_name": facts.get("direct_employer_name", "直接雇佣人待补充"),
            "direct_employer_gender": facts.get("direct_employer_gender", "性别待补充"),
            "direct_employer_birth_date": facts.get("direct_employer_birth_date", "出生日期待补充"),
            "direct_employer_ethnicity": facts.get("direct_employer_ethnicity", "民族待补充"),
            "direct_employer_id_number": facts.get("direct_employer_id_number", "身份证号待补充"),
            "direct_employer_address": facts.get("direct_employer_address", "住址待补充"),
            "direct_employer_phone": facts.get("direct_employer_phone", "联系电话待补充"),
            "contractor_name": facts.get("contractor_name", "施工总承包单位待补充"),
            "contractor_credit_code": facts.get("contractor_credit_code", "统一社会信用代码待补充"),
            "contractor_address": facts.get("contractor_address", "住所地待补充"),
            "contractor_legal_rep": facts.get("contractor_legal_rep", "法定代表人待补充"),
            "contractor_phone": facts.get("contractor_phone", "联系电话待补充"),
            "subcontractor_name": facts.get("subcontractor_name", facts.get("company_name") or structured["employer_name"]),
            "subcontractor_credit_code": facts.get("subcontractor_credit_code", "统一社会信用代码待补充"),
            "subcontractor_address": facts.get("subcontractor_address", "住所地待补充"),
            "subcontractor_legal_rep": facts.get("subcontractor_legal_rep", "法定代表人待补充"),
            "subcontractor_phone": facts.get("subcontractor_phone", "联系电话待补充"),
            "guarantor_name": facts.get("guarantor_name", "担保方待补充"),
            "guarantor_credit_code": facts.get("guarantor_credit_code", "统一社会信用代码待补充"),
            "guarantor_address": facts.get("guarantor_address", "住所地待补充"),
            "guarantor_legal_rep": facts.get("guarantor_legal_rep", "法定代表人待补充"),
            "guarantor_phone": facts.get("guarantor_phone", "联系电话待补充"),
            "amount": amount,
            "claim_amount": amount,
            "claim_amount_cn": self._number_to_chinese_upper(amount),
            "job_title": facts.get("job_title", "务工人员"),
            "start_date": facts.get("start_date", "待补充"),
            "end_date": facts.get("end_date", "待补充"),
            "work_start_date": facts.get("start_date", "待补充"),
            "work_end_date": facts.get("end_date", "待补充"),
            "work_unit_name": facts.get("work_unit_name") or facts.get("company_name") or structured["employer_name"],
            "project_name": facts.get("project_name", "项目名称待补充"),
            "employment_days": facts.get("employment_days", "待补充"),
            "wage_rate": facts.get("wage_rate", "待补充"),
            "wage_calculation": facts.get("wage_calculation", "待补充"),
            "dispute_type": structured["issue_type"],
            "cause_of_action": facts.get("cause_of_action", "追索劳动报酬纠纷" if structured["issue_type"] == "欠薪" else "劳务合同纠纷"),
            "dispute_summary": structured["raw_text"],
            "evidence_list": structured["evidence_items"] or ["待补充"],
            "risk_level": assessment["level"],
            "evidence_score": assessment["evidence_score"],
            "recommended_actions": case_report["recommended_actions"],
            "missing_evidence": evidence["missing_required"],
            "court_name": facts.get("court_name", "XX区人民法院"),
            "procuratorate_name": facts.get("procuratorate_name", "XX区人民检察院"),
        }
        field_checklist = self._build_field_checklist(template_name, context)

        return {
            "document_type": template_name,
            "document_text": template.render(**context),
            "context": context,
            "field_checklist": field_checklist,
        }

    def _number_to_chinese_upper(self, value: Any) -> str:
        digits = "零壹贰叁肆伍陆柒捌玖"
        units = ["", "拾", "佰", "仟"]
        big_units = ["", "万", "亿"]
        try:
            number = int(float(str(value)))
        except (TypeError, ValueError):
            return "待补充"
        if number == 0:
            return "零元"

        parts: list[str] = []
        group_index = 0
        while number > 0:
            group = number % 10000
            if group:
                group_text = self._convert_group(group, digits, units)
                parts.append(group_text + big_units[group_index])
            number //= 10000
            group_index += 1
        return "".join(reversed(parts)) + "元"

    def _convert_group(self, number: int, digits: str, units: list[str]) -> str:
        result = ""
        zero_flag = False
        for idx in range(4):
            divisor = 10 ** (3 - idx)
            current = number // divisor
            number %= divisor
            if current == 0:
                zero_flag = bool(result)
                continue
            if zero_flag:
                result += digits[0]
                zero_flag = False
            result += digits[current] + units[3 - idx]
        return result.rstrip(digits[0])

    def _build_field_checklist(self, template_name: str, context: dict[str, Any]) -> dict[str, Any]:
        available: list[dict[str, str]] = []
        missing: list[dict[str, str]] = []
        requirements = self.TEMPLATE_REQUIREMENTS.get(template_name, [])

        for key, label, source in requirements:
            value = context.get(key)
            display_value = self._display_value(value)
            if self._is_filled(display_value):
                available.append({"field": key, "label": label, "value": display_value})
            else:
                missing.append({"field": key, "label": label, "source": source})

        total = len(requirements)
        completion_rate = round((len(available) / total) * 100) if total else 100
        return {
            "available": available,
            "missing": missing,
            "completion_rate": completion_rate,
            "is_ready": not missing,
        }

    def _display_value(self, value: Any) -> str:
        if isinstance(value, list):
            return "、".join(str(item) for item in value if str(item).strip()) or "待补充"
        return str(value).strip()

    def _is_filled(self, value: str) -> bool:
        if not value:
            return False
        placeholders = ("待补充", "待核定", "未填写")
        return not any(item in value for item in placeholders)
