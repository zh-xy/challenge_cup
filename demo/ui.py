from __future__ import annotations

import base64
import json
import os
import re
import sys
from collections import Counter
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from demo.api_client import ApiClient


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
    "payment_method",
    "mediation_status",
    "mediation_willingness",
    "arbitration_status",
    "still_employed",
    "work_address",
    "work_latitude",
    "work_longitude",
    "job_title",
    "work_start_date",
    "work_end_date",
    "unpaid_start",
    "unpaid_end",
    "amount_claimed",
    "amount_claimed_number",
    "employment_days",
    "unpaid_worker_count",
    "wage_unit",
    "uploaded_evidence_names",
    "contractor_name",
    "subcontractor_name",
    "guarantor_name",
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

DATE_STATE_KEYS = {
    "work_start_date",
    "work_end_date",
    "unpaid_start",
    "unpaid_end",
}


def render_global_styles() -> None:
    st.markdown(
        """
        <style>
        /* 政务产品化风格：深色侧栏 + 浅灰主区 + 蓝色强调 */
        :root {
            --main-bg: #f3f6fb;
            --sidebar-red: #1f365c;
            --text-main: #1f2a3d;
            --text-muted: #5b6880;
            --text-on-white: #172033;
            --text-on-white-muted: rgba(23, 32, 51, 0.72);
            --scrollbar-track: #d7deeb;
            --scrollbar-thumb: #94a3bd;
            --scrollbar-thumb-hover: #6c7f9c;
        }
        .stApp {
            background-color: var(--main-bg);
            background-image: none;
            color: var(--text-main);
            /* Firefox：滑块色 轨道色 */
            scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
            scrollbar-width: thin;
        }
        [data-testid="stHeader"] {
            background-color: var(--main-bg) !important;
            background-image: none !important;
        }
        [data-testid="stMain"] {
            background-color: var(--main-bg) !important;
            background-image: none !important;
        }
        section.main > div {
            background-color: var(--main-bg) !important;
        }
        .main .block-container,
        .main p,
        .main label,
        .main .stMarkdown,
        .main .stMarkdown p,
        .main span:not(.hero-kicker):not(.highlight-chip),
        .stCaption {
            color: var(--text-main) !important;
        }
        .block-container {
            max-width: 1360px;
            padding-top: 2rem;
            padding-bottom: 2.5rem;
        }
        .main h1, .main h2, .main h3,
        section.main h1, section.main h2, section.main h3 {
            color: var(--text-main) !important;
            letter-spacing: 0.02em;
        }
        h1 {
            font-size: 3rem !important;
            font-weight: 900 !important;
        }
        h2 {
            font-size: 2rem !important;
            font-weight: 850 !important;
        }
        h3 {
            font-size: 1.4rem !important;
            font-weight: 800 !important;
        }
        p, label, .stMarkdown, .stCaption, .stTextInput, .stTextArea, .stSelectbox, .stSlider {
            font-size: 1.05rem !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 900 !important;
            color: #1a4fa3 !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 1rem !important;
            font-weight: 700 !important;
            color: var(--text-muted) !important;
        }
        [data-testid="stSidebar"] {
            background-color: var(--sidebar-red) !important;
            background-image: none !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        /* 侧栏标题、说明、单选、指标标签等保持白字（勿对全局 * 设白，否则会与浅底下拉/按钮冲突） */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] [data-testid="stHeader"] {
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] .stCaption,
        [data-testid="stSidebar"] [data-baseweb="radio"] label,
        [data-testid="stSidebar"] [data-testid="stMetricLabel"],
        [data-testid="stSidebar"] [data-testid="stMetricValue"] {
            color: #ffffff !important;
        }
        /* 侧栏下拉与次要按钮：浅底深字 */
        [data-testid="stSidebar"] .stSelectbox label {
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div {
            background-color: #edf2fa !important;
            color: #0a0a0a !important;
            border: 1px solid rgba(0, 0, 0, 0.14) !important;
        }
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span,
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] p {
            color: #0a0a0a !important;
        }
        /* 载入样例等次要按钮：浅底深字 */
        [data-testid="stSidebar"] .stButton > button:not([kind="primary"]),
        [data-testid="stSidebar"] .stButton > button[kind="secondary"],
        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"],
        [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {
            background-color: #edf2fa !important;
            color: #0a0a0a !important;
            border: 1px solid rgba(0, 0, 0, 0.14) !important;
        }
        [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) *,
        [data-testid="stSidebar"] .stButton > button[kind="secondary"] *,
        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"] *,
        [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] * {
            color: #0a0a0a !important;
        }
        [data-testid="stSidebar"] .stSuccess,
        [data-testid="stSidebar"] .stSuccess * {
            color: #0d3d1a !important;
        }
        /* 页面右侧滚动条：固定灰色（WebKit） */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        ::-webkit-scrollbar-track {
            background: var(--scrollbar-track);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--scrollbar-thumb);
            border-radius: 8px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--scrollbar-thumb-hover);
        }
        /* 主区证据分数滑动条 */
        section.main .stSlider [data-testid="stSliderTrack"] {
            background-color: rgba(45, 24, 16, 0.28) !important;
        }
        section.main .stSlider [data-baseweb="slider"] div[data-testid="stSliderTickBar"] {
            background-color: rgba(45, 24, 16, 0.35) !important;
        }
        section.main .stSlider [data-baseweb="slider"] [role="slider"] {
            background-color: #1a4fa3 !important;
            border: 2px solid #ffffff !important;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
        }
        .hero-panel {
            background: #ffffff;
            border: 1px solid rgba(31, 54, 92, 0.16);
            border-radius: 24px;
            padding: 1.8rem 2rem;
            box-shadow: 0 10px 30px rgba(21, 34, 56, 0.08);
            margin-bottom: 1.2rem;
            color: var(--text-on-white);
        }
        .hero-kicker {
            display: inline-block;
            font-size: 0.95rem;
            font-weight: 800;
            color: #ffffff;
            background: #1a4fa3;
            border-radius: 999px;
            padding: 0.35rem 0.75rem;
            margin-bottom: 0.9rem;
        }
        .hero-title {
            font-size: 2.8rem;
            font-weight: 900;
            line-height: 1.12;
            margin: 0 0 0.6rem 0;
            color: var(--text-on-white) !important;
        }
        .hero-subtitle {
            font-size: 1.16rem;
            line-height: 1.7;
            font-weight: 600;
            margin: 0;
            color: var(--text-on-white-muted) !important;
        }
        .section-card {
            background: #ffffff;
            border: 1px solid rgba(31, 54, 92, 0.12);
            border-radius: 22px;
            padding: 1.35rem 1.2rem 1.1rem 1.2rem;
            box-shadow: 0 8px 24px rgba(21, 34, 56, 0.06);
            margin-bottom: 1rem;
            color: var(--text-on-white);
        }
        .section-title {
            font-size: 1.5rem;
            font-weight: 900;
            margin-bottom: 0.3rem;
            color: var(--text-on-white) !important;
        }
        .section-copy {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-on-white-muted) !important;
            margin-bottom: 0.8rem;
        }
        .highlight-chip {
            display: inline-block;
            margin: 0.15rem 0.45rem 0.15rem 0;
            padding: 0.36rem 0.75rem;
            border-radius: 999px;
            background: #1a4fa3;
            color: #ffffff;
            font-size: 0.92rem;
            font-weight: 800;
        }
        .demo-banner {
            background: linear-gradient(135deg, #1f365c 0%, #2a4a7f 100%);
            border-radius: 24px;
            padding: 1.2rem 1.35rem;
            margin-bottom: 1rem;
            box-shadow: 0 12px 28px rgba(31, 54, 92, 0.2);
        }
        .demo-banner-title {
            font-size: 2rem;
            font-weight: 950;
            color: #ffffff !important;
            margin: 0 0 0.35rem 0;
            line-height: 1.2;
        }
        .demo-banner-copy {
            font-size: 1.08rem;
            font-weight: 700;
            line-height: 1.7;
            color: rgba(255, 255, 255, 0.9) !important;
            margin: 0;
        }
        .demo-emphasis {
            font-size: 1.22rem;
            font-weight: 900;
            color: #1a4fa3 !important;
            margin: 0.25rem 0 0.8rem 0;
        }
        /* 覆盖 .main .stMarkdown p，保证白底卡片内为黑字 */
        .main .stMarkdown .hero-panel .hero-title {
            color: var(--text-on-white) !important;
        }
        .main .stMarkdown .hero-panel .hero-subtitle {
            color: var(--text-on-white-muted) !important;
        }
        .main .stMarkdown .section-card .section-title {
            color: var(--text-on-white) !important;
        }
        .main .stMarkdown .section-card .section-copy {
            color: var(--text-on-white-muted) !important;
        }
        .stButton > button, .stDownloadButton > button {
            min-height: 3rem;
            border-radius: 14px;
            font-size: 1.02rem;
            font-weight: 800;
            border: 1px solid rgba(45, 24, 16, 0.25);
            background: #ffffff;
            color: var(--text-on-white);
            box-shadow: none;
        }
        .stButton > button[kind="primary"] {
            background-color: #1a4fa3;
            color: #ffffff;
            border: none;
        }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 14px !important;
            background: #ffffff !important;
            border-color: rgba(45, 24, 16, 0.2) !important;
            font-size: 1.08rem !important;
            color: var(--text-on-white) !important;
        }
        .stTextInput input::placeholder, .stTextArea textarea::placeholder {
            color: rgba(0, 0, 0, 0.42) !important;
        }
        .stSelectbox [data-baseweb="select"] span,
        .stMultiSelect [data-baseweb="select"] span {
            color: var(--text-on-white) !important;
        }
        .stExpander {
            border-radius: 16px !important;
            border: 1px solid rgba(31, 54, 92, 0.12) !important;
            background: #f7f9fd !important;
            color: var(--text-on-white) !important;
        }
        .stExpander summary, .streamlit-expanderHeader {
            color: var(--text-on-white) !important;
        }
        .stExpander .stMarkdown, .stExpander .stMarkdown p {
            color: var(--text-on-white) !important;
        }
        div[data-testid="stDataFrame"] {
            color: var(--text-on-white) !important;
        }
        [data-testid="stJson"] {
            color: var(--text-on-white) !important;
        }
        pre code, .stCodeBlock {
            color: var(--text-on-white) !important;
            background: #f7f9fd !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_hero(title: str, subtitle: str, tags: list[str]) -> None:
    tags_html = "".join(f'<span class="highlight-chip">{tag}</span>' for tag in tags)
    st.markdown(
        f"""
        <section class="hero-panel">
            <div class="hero-kicker">平台运行中</div>
            <div class="hero-title">{title}</div>
            <p class="hero-subtitle">{subtitle}</p>
            <div style="margin-top: 0.9rem;">{tags_html}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def section_intro(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">{title}</div>
            <div class="section-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_banner(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <section class="demo-banner">
            <div class="demo-banner-title">{title}</div>
            <p class="demo-banner-copy">{copy}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_emphasis(text: str) -> None:
    st.markdown(f'<div class="demo-emphasis">{text}</div>', unsafe_allow_html=True)


def init_state() -> None:
    defaults = {
        "case_title": "工地木工欠薪线索（默认示例）",
        "case_description": "我于2025年10月至2026年1月在某建筑劳务公司从事木工，工作地点在海淀区某工地。2025年11月至2026年1月工资未按约支付，累计欠薪24000元。已多次协商未果，现提交线索并申请协助维权。",
        "evidence_text": "身份证明\n考勤记录或工作记录\n聊天记录\n工作照片",
        "facts_json": "{}",
        "selected_template": "support_prosecution_application",
        "analysis_report": None,
        "generated_document": None,
        "last_submission": None,
        "sample_choice": "手动输入",
        "api_base_url": DEFAULT_API_BASE_URL,
        "worker_name": "张某",
        "worker_id_number": "110101199203156718",
        "worker_phone": "13812345678",
        "worker_gender": "男",
        "worker_birth_date": "1992-03-15",
        "worker_ethnicity": "汉族",
        "worker_address": "四川省达州市通川区XX镇XX村",
        "employment_sector": "工程建设领域",
        "employer_name": "某建筑劳务有限公司",
        "employer_phone": "010-62345678",
        "payment_method": "月结",
        "mediation_status": "进行中",
        "mediation_willingness": "愿意调解",
        "arbitration_status": "未进行",
        "still_employed": "否",
        "work_address": "北京市海淀区中关村街道XX建设项目",
        "work_latitude": "39.9834",
        "work_longitude": "116.3229",
        "job_title": "木工",
        "work_start_date": date(2025, 10, 1),
        "work_end_date": date(2026, 1, 31),
        "unpaid_start": date(2025, 11, 1),
        "unpaid_end": date(2026, 1, 31),
        "amount_claimed": "24000",
        "amount_claimed_number": 24000.0,
        "employment_days": 120,
        "unpaid_worker_count": 6,
        "wage_unit": "元",
        "uploaded_evidence_names": ["工资表截图.pdf", "工地考勤照片.jpg"],
        "contractor_name": "北京某建设集团有限公司",
        "subcontractor_name": "北京某劳务分包有限公司",
        "guarantor_name": "某项目工资支付担保机构",
        "required_evidence_selected": ["劳动合同", "工资清单", "公示牌照片"],
        "practical_evidence_selected": ["聊天记录", "证人证言", "门禁卡"],
        "selected_submission_id": "",
        "review_case_status": "已受理，待检察评估",
        "review_mediation_priority": "可诉前再协调",
        "review_prosecution_necessity": "需补充事实后再评估",
        "review_prosecutor_note": "已核验当事人基本劳动关系线索，建议先补齐工资约定依据与欠薪流水，再进行支持起诉必要性复评。",
        "review_user_message": "请补充近三个月工资发放记录、与班组长确认工资标准的聊天记录，并保留原始截图时间信息。",
        "review_relief_labor_complaint": True,
        "review_relief_labor_arbitration": False,
        "review_relief_legal_aid": True,
        "review_relief_union_or_street_help": True,
        "review_relief_note": "已向劳动监察投诉并完成受理登记；街道调解已组织一次协商未达成一致；法律援助已完成初审。",
        "review_mediation_case_type": "双方有明确调解意愿型",
        "review_prosecution_case_type": "维权能力严重欠缺型",
        "qa_question": "老板拖欠我三个月工资，没有签劳动合同，只有聊天记录和考勤照片，下一步怎么维权？",
        "qa_answer": {
            "summary": "建议先固定劳动关系与欠薪金额证据，优先走劳动监察或劳动仲裁；若存在批量欠薪、弱势群体维权能力不足或执行困难，再申请检察支持起诉。",
            "question_type": "欠薪维权路径",
            "scene": "欠薪",
            "steps": [
                "整理时间线：入职时间、欠薪起止时间、每月应发与实发金额。",
                "先向劳动监察投诉并保留受理回执，同步准备仲裁材料。",
                "补齐关键证据后提交仲裁；如执行风险高，可同步申请检察支持起诉。"
            ],
            "materials": [
                "身份证明、考勤记录、工资约定证据",
                "聊天记录原图及导出记录",
                "工资流水或欠薪明细表"
            ],
            "risk_tip": "注意保留原始证据文件和形成时间，避免仅提交转发截图导致证明力下降。",
            "legal_basis": [
                {"title": "《劳动合同法》第三十条", "summary": "用人单位应当及时足额支付劳动报酬。"},
                {"title": "《劳动争议调解仲裁法》", "summary": "劳动者可通过仲裁程序主张劳动报酬和相关权益。"}
            ]
        },
        "query_submission_id": "SUB-0001",
        "queried_case": None,
        "prosecutor_template_choice": "support_prosecution_opinion_non_construction",
        "prosecutor_document_preview": None,
        "last_action": "",
        "_review_synced_submission_id": "SUB-0001",
        "patch_company_credit_code": "91110108MA01ABCDE1",
        "patch_company_address": "北京市海淀区XX路88号",
        "patch_company_legal_rep": "李某某",
        "patch_company_phone": "010-62118888",
        "patch_direct_employer_name": "王某（班组长）",
        "patch_direct_employer_id_number": "110101198805068877",
        "patch_contractor_name": "北京某建设集团有限公司",
        "patch_subcontractor_name": "北京某劳务分包有限公司",
        "patch_guarantor_name": "某工程保证担保有限公司",
        "patch_employment_days": "118",
        "patch_wage_rate": "400元/天",
        "patch_wage_calculation": "按出勤天数月结，次月15日前支付",
        "patch_court_name": "北京市海淀区人民法院",
        "patch_procuratorate_name": "北京市海淀区人民检察院",
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
            value = restored_state[key]
            if key in DATE_STATE_KEYS:
                st.session_state[key] = parse_date_value(value)
            else:
                st.session_state[key] = value


def persist_state_to_query_params() -> None:
    state_payload: dict[str, Any] = {}
    for key in PERSISTED_STATE_KEYS:
        value = st.session_state.get(key)
        if isinstance(value, date):
            state_payload[key] = value.isoformat()
        else:
            state_payload[key] = value
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
    st.session_state["work_start_date"] = parse_date_value(facts.get("start_date"))
    st.session_state["work_end_date"] = parse_date_value(facts.get("end_date"))
    sample_amount = str(facts.get("amount", "0"))
    st.session_state["amount_claimed"] = sample_amount
    try:
        st.session_state["amount_claimed_number"] = float(sample_amount)
    except ValueError:
        st.session_state["amount_claimed_number"] = 0.0
    st.session_state["required_evidence_selected"] = [item for item in sample.get("provided_evidence", []) if item in REQUIRED_EVIDENCE_OPTIONS]
    st.session_state["practical_evidence_selected"] = [item for item in sample.get("provided_evidence", []) if item in PRACTICAL_EVIDENCE_OPTIONS]
    st.session_state["analysis_report"] = None
    st.session_state["generated_document"] = None
    st.session_state["last_submission"] = None


def parse_facts(raw_facts: str) -> dict[str, Any]:
    text = raw_facts.strip()
    if not text:
        return {}
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("补充事实必须是 JSON 对象。")
    return parsed


def parse_date_value(value: Any) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return date.today()
    return date.today()


def format_year_month(value: Any) -> str:
    if isinstance(value, date):
        return value.strftime("%Y-%m")
    return str(value or "")


def is_valid_phone(phone: str) -> bool:
    if not phone:
        return True
    mobile_pattern = r"^1[3-9]\d{9}$"
    landline_pattern = r"^(0\d{2,3}-?)?\d{7,8}$"
    return bool(re.match(mobile_pattern, phone) or re.match(landline_pattern, phone))


def build_structured_payload(extra_facts: dict[str, Any]) -> dict[str, Any]:
    worker_name = st.session_state["worker_name"].strip()
    employer_name = st.session_state["employer_name"].strip()
    amount_claimed = st.session_state["amount_claimed"].strip()
    work_start_date = format_year_month(st.session_state["work_start_date"])
    work_end_date = format_year_month(st.session_state["work_end_date"])
    unpaid_start = format_year_month(st.session_state["unpaid_start"])
    unpaid_end = format_year_month(st.session_state["unpaid_end"])
    job_title = st.session_state["job_title"].strip()
    work_address = st.session_state["work_address"].strip()
    required_evidence = list(st.session_state["required_evidence_selected"])
    practical_evidence = list(st.session_state["practical_evidence_selected"])
    manual_evidence = [line.strip() for line in st.session_state["evidence_text"].splitlines() if line.strip()]
    uploaded_evidence = list(st.session_state.get("uploaded_evidence_names", []))

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
        "payment_method": st.session_state["payment_method"],
        "mediation_status": st.session_state["mediation_status"],
        "mediation_willingness": st.session_state["mediation_willingness"],
        "arbitration_status": st.session_state["arbitration_status"],
        "still_employed": st.session_state["still_employed"],
        "work_address": work_address,
        "work_latitude": st.session_state["work_latitude"],
        "work_longitude": st.session_state["work_longitude"],
        "job_title": job_title,
        "work_start_date": work_start_date,
        "work_end_date": work_end_date,
        "unpaid_start": unpaid_start,
        "unpaid_end": unpaid_end,
        "amount_claimed": amount_claimed,
        "employment_days": st.session_state["employment_days"],
        "unpaid_worker_count": st.session_state["unpaid_worker_count"],
    }
    evidence_catalog = {
        "required": required_evidence,
        "practical": practical_evidence,
        "manual": manual_evidence,
        "uploaded": uploaded_evidence,
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
        "payment_method": st.session_state["payment_method"],
        "mediation_status": st.session_state["mediation_status"],
        "mediation_willingness": st.session_state["mediation_willingness"],
        "arbitration_status": st.session_state["arbitration_status"],
        "still_employed": st.session_state["still_employed"],
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
        "employment_days": str(st.session_state["employment_days"] or ""),
        "unpaid_worker_count": str(st.session_state["unpaid_worker_count"] or ""),
        "wage_unit": st.session_state["wage_unit"],
    }
    if st.session_state["employment_sector"] == "工程建设领域":
        facts["contractor_name"] = st.session_state["contractor_name"].strip() or extra_facts.get("contractor_name", "")
        facts["subcontractor_name"] = st.session_state["subcontractor_name"].strip() or extra_facts.get("subcontractor_name", "")
        facts["guarantor_name"] = st.session_state["guarantor_name"].strip() or extra_facts.get("guarantor_name", "")
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
    for item in uploaded_evidence:
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


def parse_amount_value(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def extract_region_label(address: str) -> str:
    text = (address or "").strip()
    if not text:
        return "未标注地区"
    match = re.search(r"(.{2,10}?(?:省|市|自治区))", text)
    if match:
        return match.group(1)
    match = re.search(r"(.{2,10}?(?:区|县))", text)
    if match:
        return match.group(1)
    return text[:8]


def classify_amount_bucket(amount: float) -> str:
    if amount < 10000:
        return "1万以下"
    if amount < 30000:
        return "1万-3万"
    if amount < 50000:
        return "3万-5万"
    return "5万以上"


def build_warning_dashboard_data(
    dashboard_items: list[dict[str, Any]],
    submissions: list[dict[str, Any]],
) -> dict[str, Any]:
    submission_map = {item.get("submission_id"): item for item in submissions}

    region_counter: Counter[str] = Counter()
    industry_counter: Counter[str] = Counter()
    amount_bucket_counter: Counter[str] = Counter()
    month_counter: Counter[str] = Counter()
    month_high_risk_counter: Counter[str] = Counter()
    employer_counter: Counter[str] = Counter()
    region_amount_total: defaultdict[str, float] = defaultdict(float)

    for item in dashboard_items:
        sid = item.get("submission_id")
        detail = submission_map.get(sid, {})
        dispute_profile = detail.get("dispute_profile", {})
        facts = detail.get("facts", {})

        amount = parse_amount_value(item.get("amount_claimed"))
        employer = str(item.get("employer_name") or "未知主体")
        industry = str(
            dispute_profile.get("employment_sector")
            or item.get("employment_sector")
            or "未区分"
        )
        work_address = str(
            dispute_profile.get("work_address")
            or facts.get("project_name")
            or facts.get("work_address")
            or ""
        )
        region = extract_region_label(work_address)
        month = str(item.get("submitted_at", ""))[:7] or "未知月份"

        region_counter[region] += 1
        industry_counter[industry] += 1
        amount_bucket_counter[classify_amount_bucket(amount)] += 1
        month_counter[month] += 1
        employer_counter[employer] += 1
        region_amount_total[region] += amount
        if item.get("risk_level") in {"高风险", "中风险"}:
            month_high_risk_counter[month] += 1

    repeated_employers = [
        {"主体名称": name, "案件数": count}
        for name, count in employer_counter.items()
        if name not in {"", "未知主体"} and count >= 2
    ]
    repeated_employers.sort(key=lambda x: x["案件数"], reverse=True)

    region_rows = [
        {
            "地区": region,
            "案件数": count,
            "涉案总额(元)": round(region_amount_total.get(region, 0), 2),
        }
        for region, count in region_counter.items()
    ]
    region_rows.sort(key=lambda x: x["案件数"], reverse=True)

    industry_rows = [{"行业/领域": key, "案件数": value} for key, value in industry_counter.items()]
    industry_rows.sort(key=lambda x: x["案件数"], reverse=True)

    amount_rows = [
        {"金额区间": bucket, "案件数": amount_bucket_counter.get(bucket, 0)}
        for bucket in ["1万以下", "1万-3万", "3万-5万", "5万以上"]
    ]

    month_rows = [
        {
            "月份": month,
            "案件数": month_counter.get(month, 0),
            "中高风险案件": month_high_risk_counter.get(month, 0),
        }
        for month in sorted(month_counter.keys())
    ]

    alerts: list[dict[str, str]] = []
    hotspot_regions = [row for row in region_rows if row["案件数"] >= 2]
    if hotspot_regions:
        region_names = "、".join(item["地区"] for item in hotspot_regions[:3])
        alerts.append(
            {
                "level": "中高",
                "title": "区域案件聚集预警",
                "detail": f"{region_names} 出现集中申报，建议核查工程项目用工与工资支付链条。",
            }
        )
    if repeated_employers:
        top = repeated_employers[0]
        alerts.append(
            {
                "level": "高",
                "title": "重复涉案主体预警",
                "detail": f"{top['主体名称']} 已出现 {top['案件数']} 起关联案件，建议列入重点监督清单。",
            }
        )
    if len(month_rows) >= 2:
        prev, curr = month_rows[-2], month_rows[-1]
        if prev["案件数"] > 0 and curr["案件数"] >= prev["案件数"] * 1.3:
            alerts.append(
                {
                    "level": "中",
                    "title": "短期增长波动预警",
                    "detail": f"{curr['月份']} 案件量较 {prev['月份']} 上升明显，建议开展专题排查。",
                }
            )

    summary_lines = [
        f"当前共监测 {len(dashboard_items)} 件案件，覆盖 {len(region_counter)} 个地区、{len(industry_counter)} 类行业场景。",
        f"中高风险案件 {sum(1 for item in dashboard_items if item.get('risk_level') in {'高风险', '中风险'})} 件。",
        f"重复涉案主体 {len(repeated_employers)} 个，金额主要集中在 1万-3万 与 3万-5万 区间。",
    ]

    return {
        "region_rows": region_rows,
        "industry_rows": industry_rows,
        "amount_rows": amount_rows,
        "month_rows": month_rows,
        "repeated_employers": repeated_employers,
        "alerts": alerts,
        "summary_lines": summary_lines,
    }


def render_warning_dashboard(analytics: dict[str, Any], total_cases: int) -> None:
    st.subheader("风险预警看板")
    st.write("**风险总览**")
    control_col1, control_col2, control_col3 = st.columns(3)
    control_col1.metric("纳入研判案件", total_cases)
    control_col2.metric("预警专题数", len(analytics["alerts"]))
    control_col3.metric("重复涉案主体", len(analytics["repeated_employers"]))

    top_industry = analytics["industry_rows"][0] if analytics["industry_rows"] else None
    if top_industry and total_cases > 0:
        ratio = round(top_industry["案件数"] * 100 / total_cases, 1)
        st.info(f"案件主要集中在「{top_industry['行业/领域']}」，占比约 {ratio}%。")

    st.write("**结构分布**")
    tab1, tab2, tab3 = st.tabs(["区域分布", "行业分布", "金额区间"])
    with tab1:
        st.dataframe(analytics["region_rows"], use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(analytics["industry_rows"], use_container_width=True, hide_index=True)
        st.bar_chart(analytics["industry_rows"], x="行业/领域", y="案件数")
    with tab3:
        st.bar_chart(analytics["amount_rows"], x="金额区间", y="案件数")

    st.write("**趋势分析**")
    st.dataframe(analytics["month_rows"], use_container_width=True, hide_index=True)
    if analytics["month_rows"]:
        st.line_chart(analytics["month_rows"], x="月份", y=["案件数", "中高风险案件"])

    st.write("**预警摘要**")
    for line in analytics["summary_lines"]:
        st.write(f"- {line}")
    if analytics["alerts"]:
        for alert in analytics["alerts"]:
            st.warning(f"[{alert['level']}] {alert['title']}：{alert['detail']}")
    else:
        st.info("当前未触发明显异常波动，建议持续观察趋势变化。")

    st.write("**复核说明**")
    st.caption("预警阈值按当前演示数据自动计算，结果用于辅助研判，不替代人工业务判断。")


def render_route_cards(routes: list[dict[str, str]]) -> None:
    st.write("**推荐维权路径**")
    for route in routes:
        st.markdown(
            f"""
            <div class="section-card" style="padding: 1rem 1rem 0.8rem 1rem; margin-bottom: 0.8rem;">
                <div class="section-title" style="font-size: 1.18rem;">{route["title"]}</div>
                <div class="section-copy" style="margin-bottom: 0;">{route["copy"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_qa_panel() -> None:
    section_intro("智能法律咨询", "围绕欠薪、未签合同、工伤等高频问题给出结构化建议，提升咨询效率与办理可操作性。")
    st.text_area(
        "输入法律问题",
        key="qa_question",
        height=120,
        placeholder="例如：老板拖欠我三个月工资，没有合同，只有微信聊天记录和考勤照片，我该怎么办？",
    )
    if st.button("获取法律建议", use_container_width=True):
        question = st.session_state["qa_question"].strip()
        if not question:
            st.warning("请先输入法律问题。")
        else:
            st.session_state["qa_answer"] = ask_legal_question(question)

    qa_answer = st.session_state.get("qa_answer")
    if qa_answer:
        st.write("**咨询结论**")
        st.info(qa_answer.get("summary", "暂无结论"))
        qa_col1, qa_col2 = st.columns(2)
        qa_col1.write("**问题类型**")
        qa_col1.write(qa_answer.get("question_type", "通用咨询"))
        qa_col2.write("**对应场景**")
        qa_col2.write(qa_answer.get("scene", "欠薪"))

        st.write("**建议步骤**")
        for item in qa_answer.get("steps", []):
            st.write(f"- {item}")

        st.write("**建议准备材料**")
        for item in qa_answer.get("materials", []):
            st.write(f"- {item}")

        st.write("**风险提示**")
        st.warning(qa_answer.get("risk_tip", "请结合具体证据情况进一步核实。"))

        laws = qa_answer.get("legal_basis", [])
        if laws:
            st.write("**相关法律依据**")
            for law in laws:
                st.write(f"- {law['title']}：{law['summary']}")


def render_case_query_panel() -> None:
    section_intro("我的案件进度", "农民工可根据案件编号独立查询办理进度、检察反馈和当前建议，不依赖当前浏览器会话。")
    query_col1, query_col2 = st.columns([2, 1])
    query_col1.text_input("案件编号", key="query_submission_id", placeholder="例如：SUB-0005")
    if query_col2.button("查询进度", use_container_width=True):
        submission_id = st.session_state["query_submission_id"].strip()
        if not submission_id:
            st.warning("请先输入案件编号。")
        else:
            case_detail = safe_get(f"/cases/{submission_id}", {})
            st.session_state["queried_case"] = case_detail or None

    queried_case = st.session_state.get("queried_case")
    if not queried_case:
        st.info("输入案件编号后，可查看案件状态、检察反馈、前置救济核验和补证建议。")
        return

    status_col1, status_col2, status_col3 = st.columns(3)
    status_col1.metric("案件状态", queried_case.get("case_status", "未获取"))
    status_col2.metric("调解优先", queried_case.get("mediation_priority", "待评估"))
    status_col3.metric("起诉必要性", queried_case.get("prosecution_necessity", "待评估"))

    st.write("**案件基本信息**")
    st.table(
        [
            {
                "案件编号": queried_case.get("submission_id", "未获取"),
                "劳动者": queried_case.get("user_profile", {}).get("name", "未填"),
                "联系电话": queried_case.get("user_profile", {}).get("phone", "未填"),
                "用工主体": queried_case.get("dispute_profile", {}).get("employer_name", "未填"),
                "最近更新": queried_case.get("updated_at", "未更新"),
            }
        ]
    )

    feedback_messages = queried_case.get("feedback_messages", [])
    if feedback_messages:
        st.write("**检察院回传反馈**")
        for item in feedback_messages:
            st.write(f"- {item['sent_at']} | {item['message']}")

    relief_checks = queried_case.get("relief_checks", {})
    st.write("**前置救济核验情况**")
    st.table(
        [
            {
                "劳动监察": "已核验" if relief_checks.get("labor_complaint") else "未核验",
                "劳动仲裁": "已核验" if relief_checks.get("labor_arbitration") else "未核验",
                "法律援助": "已核验" if relief_checks.get("legal_aid") else "未核验",
                "工会/街道协助": "已核验" if relief_checks.get("union_or_street_help") else "未核验",
            }
        ]
    )
    if queried_case.get("relief_note"):
        st.caption(f"核验说明：{queried_case['relief_note']}")

    evidence_advice = build_evidence_advice(queried_case)
    if evidence_advice:
        st.write("**当前补证与调取建议**")
        st.table(evidence_advice)


def render_field_checklist(field_checklist: dict[str, Any]) -> None:
    if not field_checklist:
        return
    st.write("**模板字段完备度**")
    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("完备度", f"{field_checklist.get('completion_rate', 0)}%")
    metric_col2.metric("是否可直接定稿", "是" if field_checklist.get("is_ready") else "否")

    available = field_checklist.get("available", [])
    missing = field_checklist.get("missing", [])
    if available:
        st.write("**已掌握信息**")
        st.table(available)
    if missing:
        st.write("**待补充 / 待调取信息**")
        st.table(missing)


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


def sync_review_state(case_detail: dict[str, Any]) -> None:
    if not case_detail:
        return
    relief_checks = case_detail.get("relief_checks", {})
    st.session_state["review_case_status"] = case_detail.get("case_status", "已受理，待检察评估")
    st.session_state["review_mediation_priority"] = case_detail.get("mediation_priority", "待评估")
    st.session_state["review_prosecution_necessity"] = case_detail.get("prosecution_necessity", "待评估")
    st.session_state["review_prosecutor_note"] = case_detail.get("prosecutor_note", "") or "已初步核验劳动关系线索，建议补齐工资约定和欠薪流水后进入支持起诉必要性复评。"
    latest_feedback = ""
    feedback_messages = case_detail.get("feedback_messages", [])
    if feedback_messages:
        latest_feedback = str(feedback_messages[-1].get("message", ""))
    st.session_state["review_user_message"] = latest_feedback or "请在3个工作日内补充工资约定依据、近三个月工资流水和关键聊天原图，补齐后可优先进入文书生成。"
    st.session_state["review_relief_labor_complaint"] = bool(relief_checks.get("labor_complaint"))
    st.session_state["review_relief_labor_arbitration"] = bool(relief_checks.get("labor_arbitration"))
    st.session_state["review_relief_legal_aid"] = bool(relief_checks.get("legal_aid"))
    st.session_state["review_relief_union_or_street_help"] = bool(relief_checks.get("union_or_street_help"))
    st.session_state["review_relief_note"] = case_detail.get("relief_note", "") or "劳动监察已受理登记，街道组织过一次协调；建议同步保留受理回执与调解记录。"
    st.session_state["review_mediation_case_type"] = case_detail.get("mediation_case_type", "未分类") or "双方有明确调解意愿型"
    st.session_state["review_prosecution_case_type"] = case_detail.get("prosecution_case_type", "未分类") or "维权能力严重欠缺型"
    facts = case_detail.get("facts", {})
    st.session_state["patch_company_credit_code"] = facts.get("company_credit_code", "") or "91110108MA01ABCDE1"
    st.session_state["patch_company_address"] = facts.get("company_address", "") or "北京市海淀区XX路88号"
    st.session_state["patch_company_legal_rep"] = facts.get("company_legal_rep", "") or "李某某"
    st.session_state["patch_company_phone"] = facts.get("company_phone", "") or "010-62118888"
    st.session_state["patch_direct_employer_name"] = facts.get("direct_employer_name", "") or "王某（班组长）"
    st.session_state["patch_direct_employer_id_number"] = facts.get("direct_employer_id_number", "") or "110101198805068877"
    st.session_state["patch_contractor_name"] = facts.get("contractor_name", "") or "某建设集团有限公司"
    st.session_state["patch_subcontractor_name"] = facts.get("subcontractor_name", "") or "某劳务分包有限公司"
    st.session_state["patch_guarantor_name"] = facts.get("guarantor_name", "") or "某工程保证担保有限公司"
    st.session_state["patch_employment_days"] = facts.get("employment_days", "") or "118"
    st.session_state["patch_wage_rate"] = facts.get("wage_rate", "") or "400元/天"
    st.session_state["patch_wage_calculation"] = facts.get("wage_calculation", "") or "按出勤天数月结，次月15日前支付"
    st.session_state["patch_court_name"] = facts.get("court_name", "") or "北京市海淀区人民法院"
    st.session_state["patch_procuratorate_name"] = facts.get("procuratorate_name", "") or "北京市海淀区人民检察院"


def render_sidebar() -> str:
    st.sidebar.title("平台控制台")
    view = st.sidebar.radio("视图切换", options=[VIEW_USER, VIEW_ADMIN])
    st.sidebar.caption("页面统一通过后端 API 获取结果，确保接口边界清晰、运行可追踪。")
    st.sidebar.text_input("后端地址", key="api_base_url")

    sample_cases = safe_get("/cases/samples", {"items": []}).get("items", [])
    sample_options = {"手动输入": None}
    sample_options.update({f'{item["case_id"]} | {item["title"]}': item for item in sample_cases})

    st.sidebar.divider()
    st.sidebar.subheader("标准样例库")
    selected_label = st.sidebar.selectbox("快速载入样例", options=list(sample_options.keys()), key="sample_choice")
    if st.sidebar.button("载入案例", use_container_width=True) and sample_options[selected_label]:
        load_sample_into_state(sample_options[selected_label])
        st.sidebar.success("样例已载入输入区。")

    st.sidebar.divider()
    dashboard = safe_get("/prosecutor/dashboard", {"total_cases": 0, "high_evidence_cases": 0})
    st.sidebar.metric("后台案件总数", dashboard.get("total_cases", 0))
    st.sidebar.metric("高证据案件", dashboard.get("high_evidence_cases", 0))
    return view


def render_user_view() -> None:
    render_status_banner(
        "农民工服务端",
        "入口统一采集案件信息、证据线索与补充材料，结果由后端规则引擎与文书模块统一返回，支持稳定运行与持续迭代。",
    )
    render_page_hero(
        "农民工维权入口",
        "围绕真实办案流程组织采集字段，确保前端输入可直接进入分析、文书生成与检察院协同流程。",
        ["流程闭环", "字段规范", "接口稳定"],
    )
    render_emphasis("当前页面支持从线索采集到后台流转的全流程闭环。")

    left_col, right_col = st.columns([1.1, 1])

    with left_col:
        section_intro("填写案件信息", "前端按个人信息、欠薪线索、证据情况分段采集，降低填报门槛，也方便检察院后台直接研判。")
        st.text_input("案件标题（可选）", key="case_title", placeholder="例如：工地欠薪三个月")

        st.write("**一、劳动者基本信息**")
        base_col1, base_col2 = st.columns(2)
        base_col1.text_input("姓名", key="worker_name", placeholder="例如：张某")
        base_col2.text_input("联系电话", key="worker_phone", placeholder="例如：13800000000")
        base_col3, base_col4 = st.columns(2)
        base_col3.text_input("身份证号码", key="worker_id_number", placeholder="可选填")
        base_col4.selectbox("性别", options=["未填写", "男", "女"], key="worker_gender")
        base_col5, base_col6 = st.columns(2)
        base_col5.text_input("出生日期", key="worker_birth_date", placeholder="例如：1990-01-01")
        base_col6.text_input("民族", key="worker_ethnicity", placeholder="例如：汉族")
        st.text_input("住所地", key="worker_address", placeholder="例如：四川省某市某县")

        st.write("**二、欠薪线索采集**")
        clue_col1, clue_col2 = st.columns(2)
        clue_col1.selectbox("工作领域", options=["工程建设领域", "非工程建设领域"], key="employment_sector")
        clue_col2.text_input("拖欠工资单位名称", key="employer_name", placeholder="例如：某建筑劳务公司")
        clue_col11, clue_col12 = st.columns(2)
        clue_col11.selectbox("工资结算方式", options=["日结", "月结", "计件", "完工结"], key="payment_method")
        clue_col12.selectbox("后续是否仍在原单位就业", options=["是", "否"], key="still_employed")
        clue_col13, clue_col14, clue_col15 = st.columns(3)
        clue_col13.selectbox("调解情况", options=["未进行", "进行中", "已完成"], key="mediation_status")
        clue_col14.selectbox("调解意愿", options=["愿意调解", "不愿调解", "待定"], key="mediation_willingness")
        clue_col15.selectbox("劳动争议仲裁情况", options=["未进行", "申请中", "已裁决"], key="arbitration_status")
        clue_col3, clue_col4 = st.columns(2)
        clue_col3.text_input("拖欠工资单位电话", key="employer_phone", placeholder="可选填")
        clue_col4.text_input("实际工作地址", key="work_address", placeholder="例如：某区某工地")
        locate_col1, locate_col2, locate_col3 = st.columns(3)
        if locate_col1.button("自动定位填充", use_container_width=True):
            st.session_state["work_address"] = st.session_state["work_address"] or "北京市海淀区中关村街道XX工地"
            st.session_state["work_latitude"] = "39.9834"
            st.session_state["work_longitude"] = "116.3229"
        locate_col2.text_input("纬度（自动填充）", key="work_latitude")
        locate_col3.text_input("经度（自动填充）", key="work_longitude")
        clue_col5, clue_col6 = st.columns(2)
        clue_col5.text_input("从事工种/工作内容", key="job_title", placeholder="例如：木工")
        clue_col6.number_input("主张金额", min_value=0.0, step=100.0, key="amount_claimed_number")
        unit_col1, unit_col2, unit_col3 = st.columns(3)
        unit_col1.number_input("总工作时长（天）", min_value=0, step=1, key="employment_days")
        unit_col2.number_input("欠薪涉及人数", min_value=1, step=1, key="unpaid_worker_count")
        unit_col3.selectbox("金额单位", options=["元", "万元"], key="wage_unit")
        clue_col7, clue_col8 = st.columns(2)
        clue_col7.date_input("工作开始时间", key="work_start_date")
        clue_col8.date_input("工作结束时间", key="work_end_date")
        clue_col9, clue_col10 = st.columns(2)
        clue_col9.date_input("欠薪起始时间", key="unpaid_start")
        clue_col10.date_input("欠薪截止时间", key="unpaid_end")
        if st.session_state["employment_sector"] == "工程建设领域":
            st.caption("工程建设领域补充信息（条件渲染）")
            eng_col1, eng_col2, eng_col3 = st.columns(3)
            eng_col1.text_input("施工总承包单位", key="contractor_name", placeholder="可从维权告示牌获取")
            eng_col2.text_input("分包单位", key="subcontractor_name", placeholder="可选填")
            eng_col3.text_input("担保方", key="guarantor_name", placeholder="可选填")
        st.text_area(
            "欠薪基本情况概要",
            key="case_description",
            height=220,
            placeholder="可按模板填写：本人于XX年XX月至XX年XX月在XX单位从事XX工作，自XX年XX月开始被拖欠工资，目前共被拖欠XXXX元。",
        )

        st.write("**三、证据情况与补充材料**")
        st.multiselect(
            "应然证据",
            options=REQUIRED_EVIDENCE_OPTIONS,
            key="required_evidence_selected",
            help="根据制度设计通常应当留存的证据。",
        )
        st.multiselect(
            "实然证据",
            options=PRACTICAL_EVIDENCE_OPTIONS,
            key="practical_evidence_selected",
            help="实践中常见、可辅助证明劳动关系和欠薪事实的证据。",
        )
        st.text_area(
            "其他已有证据（每行一项，可选）",
            key="evidence_text",
            height=120,
            placeholder="身份证明\n考勤记录或工作记录\n工作照片",
        )
        uploaded_files = st.file_uploader(
            "上传证据材料（图片/文档/音视频）",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg", "pdf", "doc", "docx", "mp4", "mp3", "wav", "txt"],
        )
        st.session_state["uploaded_evidence_names"] = [file.name for file in (uploaded_files or [])]
        if st.session_state["uploaded_evidence_names"]:
            st.caption("已选择文件：" + "；".join(st.session_state["uploaded_evidence_names"]))
        with st.expander("补充事实（JSON，可选）"):
            st.text_area(
                "用于增强文书生成上下文，例如 worker_name / company_name / amount",
                key="facts_json",
                height=180,
            )
        st.selectbox(
            "文书类型",
            options=list(TEMPLATE_LABELS.keys()),
            key="selected_template",
            format_func=lambda value: TEMPLATE_LABELS[value],
        )

        button_col1, button_col2, button_col3 = st.columns(3)
        analyze_clicked = button_col1.button("一键分析", type="primary", use_container_width=True)
        generate_clicked = button_col2.button("生成文书", use_container_width=True)
        submit_clicked = button_col3.button("保存到后台", use_container_width=True)

    action_report: dict[str, Any] | None = None
    if analyze_clicked or generate_clicked or submit_clicked:
        st.session_state["amount_claimed"] = str(int(st.session_state.get("amount_claimed_number", 0)))
        if not st.session_state["worker_name"].strip() or not st.session_state["worker_phone"].strip():
            st.warning("请至少填写劳动者姓名和联系电话。")
        elif not is_valid_phone(st.session_state["worker_phone"].strip()):
            st.warning("联系电话格式有误，请填写11位手机号或固定电话。")
        elif st.session_state["employer_phone"].strip() and not is_valid_phone(st.session_state["employer_phone"].strip()):
            st.warning("单位联系电话格式有误，请检查后重试。")
        elif not st.session_state["employer_name"].strip() or not st.session_state["case_description"].strip():
            st.warning("请填写拖欠工资单位名称和欠薪基本情况概要。")
        else:
            try:
                extra_facts = parse_facts(st.session_state["facts_json"])
            except (json.JSONDecodeError, ValueError) as exc:
                st.error(f"补充事实格式错误：{exc}")
            else:
                payload = build_structured_payload(extra_facts)
                action_report = build_analysis(payload["description"], payload["provided_evidence"], payload["facts"])
                if action_report:
                    st.session_state["analysis_report"] = action_report
                if analyze_clicked and not generate_clicked:
                    st.session_state["generated_document"] = None
                    st.session_state["last_action"] = "analysis"
                if generate_clicked and action_report:
                    st.session_state["generated_document"] = build_document(
                        action_report,
                        st.session_state["selected_template"],
                        payload["facts"],
                    )
                    st.session_state["last_action"] = "document"
                if submit_clicked:
                    st.session_state["last_submission"] = safe_post(
                        "/cases/submit",
                        {
                            "title": st.session_state["case_title"].strip() or None,
                            "description": payload["description"],
                            "provided_evidence": payload["provided_evidence"],
                            "facts": payload["facts"],
                            "user_profile": payload["user_profile"],
                            "dispute_profile": payload["dispute_profile"],
                            "evidence_catalog": payload["evidence_catalog"],
                        },
                    )
                    st.session_state["last_action"] = "submit"

    analysis_report = st.session_state.get("analysis_report")
    generated_document = st.session_state.get("generated_document")
    last_submission = st.session_state.get("last_submission")

    with right_col:
        section_intro("结果输出区", "分析结论、风险指标和文书预览统一呈现，便于业务办理和研判复核。")
        last_action = st.session_state.get("last_action", "")
        if last_action == "analysis":
            st.info("当前展示为：分析结果（未生成文书）。")
        elif last_action == "document":
            st.info("当前展示为：文书结果（基于最新分析生成）。")
        elif last_action == "submit":
            st.info("当前展示为：提交结果（已写入检察院后台）。")
        if last_submission:
            st.success(
                f"案件已进入检察后台：{last_submission['submission_id']} | "
                f"{last_submission['case_status']}"
            )
            st.write("**已同步的结构化信息**")
            st.table(
                [
                    {
                        "劳动者": last_submission["user_profile"].get("name", "未填"),
                        "联系电话": last_submission["user_profile"].get("phone", "未填"),
                        "工作领域": last_submission["dispute_profile"].get("employment_sector", "未填"),
                        "用工主体": last_submission["dispute_profile"].get("employer_name", "未填"),
                    }
                ]
            )
            if last_submission.get("feedback_messages"):
                st.write("**检察院回传提示**")
                for item in last_submission["feedback_messages"]:
                    st.write(f"- {item['sent_at']} | {item['message']}")

        if not analysis_report:
            st.info("点击“一键分析”后，这里会展示证据分数、风险等级、结构化字段和文书预览。")
            return

        assessment = analysis_report["risk_assessment"]
        structured = analysis_report["structured_data"]
        evidence = analysis_report["evidence"]

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("证据分数", assessment["evidence_score"])
        metric_col2.metric("风险等级", assessment["level"])
        metric_col3.metric("风险分数", assessment["score"])

        st.subheader("分析输出")
        st.write("**结构化字段**")
        st.table(
            [
                {
                    "劳动者": structured["worker_name"],
                    "用工主体": structured["employer_name"],
                    "纠纷类型": structured["issue_type"],
                    "涉案金额(元)": structured["amount_claimed"] or "待补充",
                    "欠薪时长(月)": structured["unpaid_duration_months"] or "待补充",
                    "是否签合同": "已签" if structured["has_contract"] is True else "未签" if structured["has_contract"] is False else "未知",
                    "是否工伤": "是" if structured["injury_occurred"] else "否",
                }
            ]
        )

        if structured["extraction_notes"]:
            st.write("**抽取提示**")
            for note in structured["extraction_notes"]:
                st.write(f"- {note}")

        st.write("**证据情况**")
        st.json(
            {
                "已识别证据": structured["evidence_items"],
                "关键缺失证据": evidence["missing_required"],
                "建议补充证据": evidence["optional_evidence"],
            }
        )

        st.write("**建议动作**")
        for action in analysis_report["recommended_actions"]:
            st.write(f"- {action}")

        render_route_cards(build_route_recommendations(analysis_report, last_submission))

        st.subheader("文书输出")
        st.write("**文书预览**")
        if generated_document:
            st.code(generated_document["document_text"], language="text")
            render_field_checklist(generated_document.get("field_checklist", {}))
            file_stem = st.session_state["case_title"].strip() or structured["issue_type"]
            st.download_button(
                "下载文书 .txt",
                data=generated_document["document_text"],
                file_name=f"{file_stem}_{generated_document['document_type']}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            st.info("点击“生成文书”后可在这里预览并下载文本版文书。")

    st.divider()
    render_qa_panel()
    st.divider()
    render_case_query_panel()


def render_admin_view() -> None:
    render_status_banner(
        "检察业务后台",
        "后台聚合案件状态、风险分布、补证建议与评估操作，支持案件分流、协同处置与持续运营。",
    )
    render_page_hero(
        "检察院决策后台",
        "围绕办案优先级和证据质量建立可视化工作台，提升线索转化效率与处置一致性。",
        ["风险分层", "状态跟踪", "协同处置"],
    )
    render_emphasis("后台数据与前端页面解耦，支持后续部署扩展与多端复用。")

    dashboard = safe_get("/prosecutor/dashboard", {"items": []})
    rows = build_case_rows(dashboard.get("items", []))

    if not rows:
        st.info("当前还没有提交案件。")
        return

    section_intro("办案总览", "先看全局态势，再进入个案研判与处置操作。")
    threshold = st.slider("证据分数阈值（筛选 > 当前值的重点案件）", min_value=0, max_value=100, value=0)
    filtered_rows = [row for row in rows if row["证据分数"] > threshold]

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("案件总数", len(rows))
    metric_col2.metric(f"证据分数 > {threshold}", len(filtered_rows))
    metric_col3.metric("高优先级案件", sum(1 for row in rows if row["优先级"] == "高证据优先关注"))

    st.write("**案件汇总表**")
    st.dataframe(filtered_rows or rows, use_container_width=True, hide_index=True)

    submissions_payload = safe_get("/cases/submissions", {"items": []})
    submissions = submissions_payload.get("items", [])
    analytics = build_warning_dashboard_data(dashboard.get("items", []), submissions)
    render_warning_dashboard(analytics, len(rows))

    st.divider()
    st.subheader("个案研判")
    available_ids = [item["submission_id"] for item in dashboard.get("items", [])]
    if available_ids and st.session_state["selected_submission_id"] not in available_ids:
        st.session_state["selected_submission_id"] = available_ids[0]

    st.write("**选择案件并处理**")
    st.selectbox("选择案件", options=available_ids, key="selected_submission_id")
    selected_case = safe_get(f"/cases/{st.session_state['selected_submission_id']}", {})
    current_submission_id = st.session_state.get("selected_submission_id", "")
    if current_submission_id and current_submission_id != st.session_state.get("_review_synced_submission_id", ""):
        sync_review_state(selected_case)
        st.session_state["_review_synced_submission_id"] = current_submission_id

    if selected_case:
        detail_col1, detail_col2 = st.columns(2)
        detail_col1.write("**劳动者与线索信息**")
        detail_col1.table(
            [
                {
                    "劳动者": selected_case["user_profile"].get("name", "未填"),
                    "联系电话": selected_case["user_profile"].get("phone", "未填"),
                    "用工主体": selected_case["dispute_profile"].get("employer_name", "未填"),
                    "工作领域": selected_case["dispute_profile"].get("employment_sector", "未填"),
                }
            ]
        )
        detail_col2.write("**当前办案状态**")
        detail_col2.table(
            [
                {
                    "案件状态": selected_case.get("case_status", "未设置"),
                    "调解优先": selected_case.get("mediation_priority", "待评估"),
                    "起诉必要性": selected_case.get("prosecution_necessity", "待评估"),
                    "调解类型": selected_case.get("mediation_case_type", "未分类") or "未分类",
                    "起诉类型": selected_case.get("prosecution_case_type", "未分类") or "未分类",
                    "最近更新": selected_case.get("updated_at", "未更新"),
                }
            ]
        )

        st.write("**第一步：前置救济核验**")
        relief_col1, relief_col2, relief_col3, relief_col4 = st.columns(4)
        relief_col1.checkbox("已走劳动监察", key="review_relief_labor_complaint")
        relief_col2.checkbox("已申请仲裁", key="review_relief_labor_arbitration")
        relief_col3.checkbox("已申请法援", key="review_relief_legal_aid")
        relief_col4.checkbox("已寻求工会/街道协助", key="review_relief_union_or_street_help")
        st.text_area(
            "前置救济核验说明",
            key="review_relief_note",
            height=90,
            placeholder="例如：已拨打12333并登记，但尚未形成实质处理结果；当事人暂无仲裁能力。",
        )

        st.write("**第二步：类型化评估**")
        review_col1, review_col2, review_col3 = st.columns(3)
        review_col1.selectbox(
            "案件状态",
            options=["已受理，待检察评估", "待补充证据", "建议优先调解", "可进入文书生成", "建议支持起诉"],
            key="review_case_status",
        )
        review_col2.selectbox(
            "调解优先判断",
            options=["待评估", "优先调解", "可诉前再协调", "不宜调解"],
            key="review_mediation_priority",
        )
        review_col3.selectbox(
            "起诉必要性",
            options=["待评估", "暂不建议支持起诉", "建议支持起诉", "需补充事实后再评估"],
            key="review_prosecution_necessity",
        )
        type_col1, type_col2 = st.columns(2)
        type_col1.selectbox(
            "调解类型",
            options=["未分类", "经营暂时困难型", "双方有明确调解意愿型", "诉讼周期劣势明显型", "涉及人数众多型"],
            key="review_mediation_case_type",
        )
        type_col2.selectbox(
            "起诉类型",
            options=["未分类", "恶意欠薪型", "不存在调解条件型", "调解失败型", "维权能力严重欠缺型"],
            key="review_prosecution_case_type",
        )

        st.write("**第三步：补证建议**")
        evidence_advice = build_evidence_advice(selected_case)
        st.table(evidence_advice)

        st.write("**第四步：文书准备与字段补录**")
        st.selectbox(
            "检察院端文书模板",
            options=list(TEMPLATE_LABELS.keys()),
            key="prosecutor_template_choice",
            format_func=lambda value: TEMPLATE_LABELS[value],
        )
        st.write("**检察院补录事实字段**")
        patch_col1, patch_col2 = st.columns(2)
        patch_col1.text_input("统一社会信用代码", key="patch_company_credit_code")
        patch_col2.text_input("单位住所地", key="patch_company_address")
        patch_col3, patch_col4 = st.columns(2)
        patch_col3.text_input("法定代表人", key="patch_company_legal_rep")
        patch_col4.text_input("单位联系电话", key="patch_company_phone")
        patch_col5, patch_col6 = st.columns(2)
        patch_col5.text_input("直接雇佣人", key="patch_direct_employer_name")
        patch_col6.text_input("直接雇佣人身份证号", key="patch_direct_employer_id_number")
        patch_col7, patch_col8, patch_col9 = st.columns(3)
        patch_col7.text_input("总包单位", key="patch_contractor_name")
        patch_col8.text_input("分包单位", key="patch_subcontractor_name")
        patch_col9.text_input("担保方", key="patch_guarantor_name")
        patch_col10, patch_col11 = st.columns(2)
        patch_col10.text_input("工作天数", key="patch_employment_days")
        patch_col11.text_input("工资标准", key="patch_wage_rate")
        st.text_input("工资计算方式", key="patch_wage_calculation")
        patch_col12, patch_col13 = st.columns(2)
        patch_col12.text_input("管辖法院", key="patch_court_name")
        patch_col13.text_input("检察院名称", key="patch_procuratorate_name")
        if st.button("保存补录信息", use_container_width=True):
            patched_case = safe_post(
                f"/cases/{st.session_state['selected_submission_id']}/facts",
                {
                    "facts_patch": {
                        "company_credit_code": st.session_state["patch_company_credit_code"],
                        "company_address": st.session_state["patch_company_address"],
                        "company_legal_rep": st.session_state["patch_company_legal_rep"],
                        "company_phone": st.session_state["patch_company_phone"],
                        "direct_employer_name": st.session_state["patch_direct_employer_name"],
                        "direct_employer_id_number": st.session_state["patch_direct_employer_id_number"],
                        "contractor_name": st.session_state["patch_contractor_name"],
                        "subcontractor_name": st.session_state["patch_subcontractor_name"],
                        "guarantor_name": st.session_state["patch_guarantor_name"],
                        "employment_days": st.session_state["patch_employment_days"],
                        "wage_rate": st.session_state["patch_wage_rate"],
                        "wage_calculation": st.session_state["patch_wage_calculation"],
                        "court_name": st.session_state["patch_court_name"],
                        "procuratorate_name": st.session_state["patch_procuratorate_name"],
                    }
                },
            )
            if patched_case:
                st.success("补录事实已回写案件，可重新生成正式文书。")

        if st.button("生成文书草稿并检查缺失字段", use_container_width=True):
            st.session_state["prosecutor_document_preview"] = safe_post(
                "/document/generate",
                {
                    "template_name": st.session_state["prosecutor_template_choice"],
                    "description": selected_case["description"],
                    "provided_evidence": selected_case.get("provided_evidence", []),
                    "facts": {
                        **selected_case.get("facts", {}),
                        "company_credit_code": st.session_state["patch_company_credit_code"],
                        "company_address": st.session_state["patch_company_address"],
                        "company_legal_rep": st.session_state["patch_company_legal_rep"],
                        "company_phone": st.session_state["patch_company_phone"],
                        "direct_employer_name": st.session_state["patch_direct_employer_name"],
                        "direct_employer_id_number": st.session_state["patch_direct_employer_id_number"],
                        "contractor_name": st.session_state["patch_contractor_name"],
                        "subcontractor_name": st.session_state["patch_subcontractor_name"],
                        "guarantor_name": st.session_state["patch_guarantor_name"],
                        "employment_days": st.session_state["patch_employment_days"],
                        "wage_rate": st.session_state["patch_wage_rate"],
                        "wage_calculation": st.session_state["patch_wage_calculation"],
                        "court_name": st.session_state["patch_court_name"],
                        "procuratorate_name": st.session_state["patch_procuratorate_name"],
                    },
                },
            )

        prosecutor_document_preview = st.session_state.get("prosecutor_document_preview")
        if prosecutor_document_preview:
            st.write("**检察院端文书草稿**")
            st.code(prosecutor_document_preview["document_text"], language="text")
            render_field_checklist(prosecutor_document_preview.get("field_checklist", {}))

        st.write("**第五步：评估结论与回传**")
        st.text_area(
            "检察院内部研判意见",
            key="review_prosecutor_note",
            height=120,
            placeholder="填写前置救济、调解意愿、起诉必要性等评估意见。",
        )
        st.text_area(
            "回传农民工端的提示",
            key="review_user_message",
            height=120,
            placeholder="例如：请优先补充聊天记录和考勤材料；若双方有协商基础，建议先调解。",
        )
        if st.button("保存评估并回传", type="primary", use_container_width=True):
            updated_case = safe_post(
                f"/cases/{st.session_state['selected_submission_id']}/review",
                {
                    "case_status": st.session_state["review_case_status"],
                    "mediation_priority": st.session_state["review_mediation_priority"],
                    "prosecution_necessity": st.session_state["review_prosecution_necessity"],
                    "prosecutor_note": st.session_state["review_prosecutor_note"],
                    "user_message": st.session_state["review_user_message"],
                    "relief_checks": {
                        "labor_complaint": st.session_state["review_relief_labor_complaint"],
                        "labor_arbitration": st.session_state["review_relief_labor_arbitration"],
                        "legal_aid": st.session_state["review_relief_legal_aid"],
                        "union_or_street_help": st.session_state["review_relief_union_or_street_help"],
                    },
                    "relief_note": st.session_state["review_relief_note"],
                    "mediation_case_type": st.session_state["review_mediation_case_type"],
                    "prosecution_case_type": st.session_state["review_prosecution_case_type"],
                },
            )
            if updated_case:
                st.success("检察院评估结果已保存，并已回传农民工端。")
                st.session_state["last_submission"] = updated_case

        if selected_case.get("feedback_messages"):
            st.write("**已回传反馈**")
            for item in selected_case["feedback_messages"]:
                st.write(f"- {item['sent_at']} | {item['message']}")

    # 删除重复且解释价值低的风险等级小图，避免干扰主看板与个案操作链路。


def main() -> None:
    st.set_page_config(page_title="农民工权益保障智能平台", layout="wide")
    restore_state_from_query_params()
    init_state()
    render_global_styles()

    st.title("农民工权益保障智能平台")
    st.caption("系统当前以 API 为核心驱动方式，支持稳定运行、功能扩展与跨端复用。")

    view = render_sidebar()
    if view == VIEW_USER:
        render_user_view()
    else:
        render_admin_view()
    persist_state_to_query_params()


if __name__ == "__main__":
    main()
