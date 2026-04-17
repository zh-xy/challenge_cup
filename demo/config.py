from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VIEW_USER = "农民工维权入口"
VIEW_ADMIN = "检察院决策后台"
DEFAULT_API_BASE_URL = os.getenv("DEMO_API_BASE_URL", "http://127.0.0.1:8000")
REQUIRED_EVIDENCE_OPTIONS = ["劳动合同", "工资清单", "保险保单", "公示牌照片"]
PRACTICAL_EVIDENCE_OPTIONS = ["门禁卡", "聊天记录", "系统记录进出的电子系统记录", "食堂消费系统记录", "证人证言"]
TEMPLATE_LABELS = {
    "arbitration_application": "劳动仲裁申请书",
    "support_prosecution_application": "支持起诉申请书",
    "civil_complaint_non_construction": "民事起诉状（非工程建设领域）",
    "civil_complaint_construction": "民事起诉状（工程建设领域）",
    "support_prosecution_opinion_non_construction": "支持起诉书（非工程建设领域）",
    "support_prosecution_opinion_construction": "支持起诉书（工程建设领域）",
}
PERSISTED_STATE_KEYS = (
    "case_title",
    "case_description",
    "evidence_text",
    "facts_json",
    "selected_template",
    "analysis_report",
    "generated_document",
    "last_submission",
    "sample_choice",
    "worker_name",
    "worker_id_number",
    "worker_phone",
    "worker_gender",
    "worker_birth_date",
    "worker_ethnicity",
    "worker_address",
    "employment_sector",
    "employer_name",
    "employer_phone",
    "work_address",
    "job_title",
    "work_start_date",
    "work_end_date",
    "unpaid_start",
    "unpaid_end",
    "amount_claimed",
    "required_evidence_selected",
    "practical_evidence_selected",
    "selected_submission_id",
    "review_case_status",
    "review_mediation_priority",
    "review_prosecution_necessity",
    "review_prosecutor_note",
    "review_user_message",
    "review_relief_labor_complaint",
    "review_relief_labor_arbitration",
    "review_relief_legal_aid",
    "review_relief_union_or_street_help",
    "review_relief_note",
    "review_mediation_case_type",
    "review_prosecution_case_type",
    "qa_question",
    "qa_answer",
    "query_submission_id",
    "queried_case",
    "prosecutor_template_choice",
    "prosecutor_document_preview",
    "patch_company_credit_code",
    "patch_company_address",
    "patch_company_legal_rep",
    "patch_company_phone",
    "patch_direct_employer_name",
    "patch_direct_employer_id_number",
    "patch_contractor_name",
    "patch_subcontractor_name",
    "patch_guarantor_name",
    "patch_employment_days",
    "patch_wage_rate",
    "patch_wage_calculation",
    "patch_court_name",
    "patch_procuratorate_name",
)
