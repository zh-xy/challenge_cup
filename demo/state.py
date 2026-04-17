from __future__ import annotations

import base64
import json
from typing import Any

import streamlit as st

from demo.backend import get_sample_cases
from demo.config import DEFAULT_API_BASE_URL, PRACTICAL_EVIDENCE_OPTIONS, PERSISTED_STATE_KEYS, REQUIRED_EVIDENCE_OPTIONS


def init_state() -> None:
    defaults = {
        "case_title": "",
        "case_description": "",
        "evidence_text": "",
        "facts_json": "{}",
        "selected_template": "support_prosecution_application",
        "analysis_report": None,
        "generated_document": None,
        "last_submission": None,
        "sample_choice": "手动输入",
        "api_base_url": DEFAULT_API_BASE_URL,
        "worker_name": "",
        "worker_id_number": "",
        "worker_phone": "",
        "worker_gender": "未填写",
        "worker_birth_date": "",
        "worker_ethnicity": "",
        "worker_address": "",
        "employment_sector": "工程建设领域",
        "employer_name": "",
        "employer_phone": "",
        "work_address": "",
        "job_title": "",
        "work_start_date": "",
        "work_end_date": "",
        "unpaid_start": "",
        "unpaid_end": "",
        "amount_claimed": "",
        "required_evidence_selected": [],
        "practical_evidence_selected": [],
        "selected_submission_id": "",
        "review_case_status": "已受理，待检察评估",
        "review_mediation_priority": "待评估",
        "review_prosecution_necessity": "待评估",
        "review_prosecutor_note": "",
        "review_user_message": "",
        "review_relief_labor_complaint": False,
        "review_relief_labor_arbitration": False,
        "review_relief_legal_aid": False,
        "review_relief_union_or_street_help": False,
        "review_relief_note": "",
        "review_mediation_case_type": "未分类",
        "review_prosecution_case_type": "未分类",
        "qa_question": "",
        "qa_answer": None,
        "query_submission_id": "",
        "queried_case": None,
        "prosecutor_template_choice": "support_prosecution_opinion_non_construction",
        "prosecutor_document_preview": None,
        "patch_company_credit_code": "",
        "patch_company_address": "",
        "patch_company_legal_rep": "",
        "patch_company_phone": "",
        "patch_direct_employer_name": "",
        "patch_direct_employer_id_number": "",
        "patch_contractor_name": "",
        "patch_subcontractor_name": "",
        "patch_guarantor_name": "",
        "patch_employment_days": "",
        "patch_wage_rate": "",
        "patch_wage_calculation": "",
        "patch_court_name": "",
        "patch_procuratorate_name": "",
        "sample_prefilled": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def restore_state_from_query_params() -> None:
    encoded_state = st.query_params.get("state")
    if not encoded_state:
        return

    try:
        payload = base64.urlsafe_b64decode(encoded_state.encode("utf-8")).decode("utf-8")
        restored_state = json.loads(payload)
    except (ValueError, json.JSONDecodeError):
        st.query_params.pop("state", None)
        return

    if not isinstance(restored_state, dict):
        st.query_params.pop("state", None)
        return

    for key in PERSISTED_STATE_KEYS:
        if key in restored_state and key not in st.session_state:
            st.session_state[key] = restored_state[key]


def persist_state_to_query_params() -> None:
    state_payload = {key: st.session_state.get(key) for key in PERSISTED_STATE_KEYS}
    serialized = json.dumps(state_payload, ensure_ascii=False, separators=(",", ":"))
    encoded_state = base64.urlsafe_b64encode(serialized.encode("utf-8")).decode("utf-8")
    st.query_params["state"] = encoded_state


def load_sample_into_state(sample: dict[str, Any]) -> None:
    facts = sample.get("facts", {})
    st.session_state["case_title"] = str(sample.get("title", ""))
    st.session_state["case_description"] = str(sample.get("description", ""))
    st.session_state["evidence_text"] = "\n".join(sample.get("provided_evidence", []))
    st.session_state["facts_json"] = json.dumps(facts, ensure_ascii=False, indent=2)
    st.session_state["worker_name"] = str(facts.get("worker_name", ""))
    st.session_state["worker_phone"] = str(facts.get("phone", ""))
    st.session_state["employment_sector"] = str(sample.get("employment_sector", "工程建设领域"))
    st.session_state["employer_name"] = str(facts.get("company_name", ""))
    st.session_state["job_title"] = str(facts.get("job_title", ""))
    st.session_state["work_start_date"] = str(facts.get("start_date", ""))
    st.session_state["work_end_date"] = str(facts.get("end_date", ""))
    st.session_state["amount_claimed"] = str(facts.get("amount", ""))
    st.session_state["required_evidence_selected"] = [
        item for item in sample.get("provided_evidence", []) if item in REQUIRED_EVIDENCE_OPTIONS
    ]
    st.session_state["practical_evidence_selected"] = [
        item for item in sample.get("provided_evidence", []) if item in PRACTICAL_EVIDENCE_OPTIONS
    ]
    st.session_state["analysis_report"] = None
    st.session_state["generated_document"] = None
    st.session_state["last_submission"] = None
    st.session_state["sample_prefilled"] = True


def auto_prefill_sample_case() -> None:
    if st.session_state.get("sample_prefilled"):
        return
    if any(st.session_state.get(key, "").strip() for key in ("worker_name", "worker_phone", "employer_name", "case_description")):
        st.session_state["sample_prefilled"] = True
        return

    sample_cases = get_sample_cases()
    if not sample_cases:
        st.session_state["sample_prefilled"] = True
        return

    load_sample_into_state(sample_cases[0])
    st.session_state["sample_choice"] = f'{sample_cases[0].get("case_id", "")} | {sample_cases[0].get("title", "")}'.strip(" |")


def parse_facts(raw_facts: str) -> dict[str, Any]:
    text = raw_facts.strip()
    if not text:
        return {}
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("补充事实必须是 JSON 对象。")
    return parsed


def build_structured_payload(extra_facts: dict[str, Any]) -> dict[str, Any]:
    worker_name = st.session_state["worker_name"].strip()
    employer_name = st.session_state["employer_name"].strip()
    amount_claimed = st.session_state["amount_claimed"].strip()
    work_start_date = st.session_state["work_start_date"].strip()
    work_end_date = st.session_state["work_end_date"].strip()
    unpaid_start = st.session_state["unpaid_start"].strip()
    unpaid_end = st.session_state["unpaid_end"].strip()
    job_title = st.session_state["job_title"].strip()
    work_address = st.session_state["work_address"].strip()
    required_evidence = list(st.session_state["required_evidence_selected"])
    practical_evidence = list(st.session_state["practical_evidence_selected"])
    manual_evidence = [line.strip() for line in st.session_state["evidence_text"].splitlines() if line.strip()]

    user_profile = {
        "name": worker_name,
        "id_number": st.session_state["worker_id_number"].strip(),
        "phone": st.session_state["worker_phone"].strip(),
        "gender": st.session_state["worker_gender"],
        "birth_date": st.session_state["worker_birth_date"].strip(),
        "ethnicity": st.session_state["worker_ethnicity"].strip(),
        "address": st.session_state["worker_address"].strip(),
    }
    dispute_profile = {
        "employment_sector": st.session_state["employment_sector"],
        "employer_name": employer_name,
        "employer_phone": st.session_state["employer_phone"].strip(),
        "work_address": work_address,
        "job_title": job_title,
        "work_start_date": work_start_date,
        "work_end_date": work_end_date,
        "unpaid_start": unpaid_start,
        "unpaid_end": unpaid_end,
        "amount_claimed": amount_claimed,
    }
    evidence_catalog = {
        "required": required_evidence,
        "practical": practical_evidence,
        "manual": manual_evidence,
    }

    facts = {
        **extra_facts,
        "worker_name": worker_name or extra_facts.get("worker_name", ""),
        "worker_gender": st.session_state["worker_gender"] if st.session_state["worker_gender"] != "未填写" else extra_facts.get("worker_gender", ""),
        "worker_birth_date": st.session_state["worker_birth_date"].strip() or extra_facts.get("worker_birth_date", ""),
        "worker_ethnicity": st.session_state["worker_ethnicity"].strip() or extra_facts.get("worker_ethnicity", ""),
        "worker_id_number": st.session_state["worker_id_number"].strip() or extra_facts.get("worker_id_number", ""),
        "worker_address": st.session_state["worker_address"].strip() or extra_facts.get("worker_address", ""),
        "worker_phone": st.session_state["worker_phone"].strip() or extra_facts.get("worker_phone", ""),
        "company_name": employer_name or extra_facts.get("company_name", ""),
        "company_phone": st.session_state["employer_phone"].strip() or extra_facts.get("company_phone", ""),
        "work_unit_name": employer_name or extra_facts.get("work_unit_name", ""),
        "project_name": work_address or extra_facts.get("project_name", ""),
        "job_title": job_title or extra_facts.get("job_title", ""),
        "start_date": work_start_date or extra_facts.get("start_date", ""),
        "end_date": work_end_date or extra_facts.get("end_date", ""),
        "direct_employer_name": extra_facts.get("direct_employer_name", employer_name or "待补充"),
        "cause_of_action": extra_facts.get(
            "cause_of_action",
            "劳务合同纠纷" if st.session_state["employment_sector"] == "工程建设领域" else "追索劳动报酬纠纷",
        ),
        "court_name": extra_facts.get("court_name", "XX区人民法院"),
        "procuratorate_name": extra_facts.get("procuratorate_name", "XX区人民检察院"),
    }
    if amount_claimed:
        facts["amount"] = amount_claimed

    description = st.session_state["case_description"].strip()
    if not description:
        description = (
            f"{worker_name or '劳动者'}在{employer_name or '相关单位'}从事{job_title or '劳务工作'}，"
            f"工作地点为{work_address or '待补充'}，"
            f"工作时间为{work_start_date or '待补充'}至{work_end_date or '待补充'}。"
            f"目前反映{unpaid_start or '待补充'}至{unpaid_end or '待补充'}存在欠薪问题，"
            f"主张金额{amount_claimed or '待补充'}元。"
        )

    provided_evidence = []
    for group in (required_evidence, practical_evidence, manual_evidence):
        for item in group:
            if item not in provided_evidence:
                provided_evidence.append(item)

    return {
        "description": description,
        "facts": facts,
        "user_profile": user_profile,
        "dispute_profile": dispute_profile,
        "evidence_catalog": evidence_catalog,
        "provided_evidence": provided_evidence,
    }


def sync_review_state(case_detail: dict[str, Any]) -> None:
    if not case_detail:
        return
    relief_checks = case_detail.get("relief_checks", {})
    st.session_state["review_case_status"] = case_detail.get("case_status", "已受理，待检察评估")
    st.session_state["review_mediation_priority"] = case_detail.get("mediation_priority", "待评估")
    st.session_state["review_prosecution_necessity"] = case_detail.get("prosecution_necessity", "待评估")
    st.session_state["review_prosecutor_note"] = case_detail.get("prosecutor_note", "")
    st.session_state["review_relief_labor_complaint"] = bool(relief_checks.get("labor_complaint"))
    st.session_state["review_relief_labor_arbitration"] = bool(relief_checks.get("labor_arbitration"))
    st.session_state["review_relief_legal_aid"] = bool(relief_checks.get("legal_aid"))
    st.session_state["review_relief_union_or_street_help"] = bool(relief_checks.get("union_or_street_help"))
    st.session_state["review_relief_note"] = case_detail.get("relief_note", "")
    st.session_state["review_mediation_case_type"] = case_detail.get("mediation_case_type", "未分类") or "未分类"
    st.session_state["review_prosecution_case_type"] = case_detail.get("prosecution_case_type", "未分类") or "未分类"
    facts = case_detail.get("facts", {})
    st.session_state["patch_company_credit_code"] = facts.get("company_credit_code", "")
    st.session_state["patch_company_address"] = facts.get("company_address", "")
    st.session_state["patch_company_legal_rep"] = facts.get("company_legal_rep", "")
    st.session_state["patch_company_phone"] = facts.get("company_phone", "")
    st.session_state["patch_direct_employer_name"] = facts.get("direct_employer_name", "")
    st.session_state["patch_direct_employer_id_number"] = facts.get("direct_employer_id_number", "")
    st.session_state["patch_contractor_name"] = facts.get("contractor_name", "")
    st.session_state["patch_subcontractor_name"] = facts.get("subcontractor_name", "")
    st.session_state["patch_guarantor_name"] = facts.get("guarantor_name", "")
    st.session_state["patch_employment_days"] = facts.get("employment_days", "")
    st.session_state["patch_wage_rate"] = facts.get("wage_rate", "")
    st.session_state["patch_wage_calculation"] = facts.get("wage_calculation", "")
    st.session_state["patch_court_name"] = facts.get("court_name", "")
    st.session_state["patch_procuratorate_name"] = facts.get("procuratorate_name", "")
