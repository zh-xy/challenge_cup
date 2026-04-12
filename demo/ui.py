from __future__ import annotations

import base64
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.service import case_store, data_processor, document_generator


VIEW_USER = "农民工维权入口"
VIEW_ADMIN = "检察院决策后台"
TEMPLATE_LABELS = {
    "arbitration_application": "劳动仲裁申请书",
    "support_prosecution_application": "支持起诉申请书",
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
)


def render_global_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 214, 102, 0.18), transparent 28%),
                linear-gradient(180deg, #f7f2e8 0%, #f3eee3 52%, #ece6d9 100%);
            color: #1f1a17;
        }
        .block-container {
            max-width: 1360px;
            padding-top: 2rem;
            padding-bottom: 2.5rem;
        }
        h1, h2, h3 {
            color: #17120f;
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
            color: #9f2d16;
        }
        [data-testid="stMetricLabel"] {
            font-size: 1rem !important;
            font-weight: 700 !important;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #17120f 0%, #2a2019 100%);
        }
        [data-testid="stSidebar"] * {
            color: #f8f1e6 !important;
        }
        .hero-panel {
            background: linear-gradient(135deg, #fffaf1 0%, #f2e3cb 100%);
            border: 1px solid rgba(110, 74, 37, 0.14);
            border-radius: 24px;
            padding: 1.8rem 2rem;
            box-shadow: 0 18px 40px rgba(82, 58, 34, 0.08);
            margin-bottom: 1.2rem;
        }
        .hero-kicker {
            display: inline-block;
            font-size: 0.95rem;
            font-weight: 800;
            color: #9f2d16;
            background: rgba(159, 45, 22, 0.1);
            border-radius: 999px;
            padding: 0.35rem 0.75rem;
            margin-bottom: 0.9rem;
        }
        .hero-title {
            font-size: 2.8rem;
            font-weight: 900;
            line-height: 1.12;
            margin: 0 0 0.6rem 0;
        }
        .hero-subtitle {
            font-size: 1.16rem;
            line-height: 1.7;
            font-weight: 600;
            margin: 0;
            color: #4b3b30;
        }
        .section-card {
            background: rgba(255, 250, 242, 0.92);
            border: 1px solid rgba(123, 93, 65, 0.14);
            border-radius: 22px;
            padding: 1.35rem 1.2rem 1.1rem 1.2rem;
            box-shadow: 0 10px 28px rgba(72, 53, 34, 0.06);
            margin-bottom: 1rem;
        }
        .section-title {
            font-size: 1.5rem;
            font-weight: 900;
            margin-bottom: 0.3rem;
            color: #17120f;
        }
        .section-copy {
            font-size: 1rem;
            font-weight: 600;
            color: #5d4b3d;
            margin-bottom: 0.8rem;
        }
        .highlight-chip {
            display: inline-block;
            margin: 0.15rem 0.45rem 0.15rem 0;
            padding: 0.36rem 0.75rem;
            border-radius: 999px;
            background: #1f1a17;
            color: #fff7eb;
            font-size: 0.92rem;
            font-weight: 800;
        }
        .stButton > button, .stDownloadButton > button {
            min-height: 3rem;
            border-radius: 14px;
            font-size: 1.02rem;
            font-weight: 800;
            border: 1px solid #cdb79d;
            background: #fff9f1;
            color: #221a14;
            box-shadow: none;
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ad341d 0%, #cf5834 100%);
            color: #fff7f2;
            border: none;
        }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 14px !important;
            background: rgba(255, 252, 247, 0.95) !important;
            font-size: 1.08rem !important;
        }
        .stExpander {
            border-radius: 16px !important;
            border: 1px solid rgba(123, 93, 65, 0.16) !important;
            background: rgba(250, 243, 231, 0.8) !important;
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
            <div class="hero-kicker">展示页面升级</div>
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
    st.session_state["case_title"] = str(sample.get("title", ""))
    st.session_state["case_description"] = str(sample.get("description", ""))
    st.session_state["evidence_text"] = "\n".join(sample.get("provided_evidence", []))
    st.session_state["facts_json"] = json.dumps(sample.get("facts", {}), ensure_ascii=False, indent=2)
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


def build_analysis(description: str, evidence_items: list[str], facts: dict[str, Any]) -> dict[str, Any]:
    return data_processor.build_case_report(description, evidence_items, facts)


def build_document(case_report: dict[str, Any], template_name: str, facts: dict[str, Any]) -> dict[str, Any]:
    return document_generator.generate(template_name, case_report, facts)


def build_case_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered_cases = sorted(cases, key=lambda item: item["submitted_at"], reverse=True)
    rows: list[dict[str, Any]] = []
    for case in ordered_cases:
        structured = case["structured_data"]
        assessment = case["risk_assessment"]
        rows.append(
            {
                "提交编号": case["submission_id"],
                "案件标题": case["title"],
                "劳动者": structured["worker_name"],
                "用工主体": structured["employer_name"],
                "纠纷类型": structured["issue_type"],
                "涉案金额(元)": structured["amount_claimed"] or 0,
                "欠薪时长(月)": structured["unpaid_duration_months"] or 0,
                "证据分数": assessment["evidence_score"],
                "风险等级": assessment["level"],
                "优先级": assessment["priority_label"],
                "提交时间": case["submitted_at"],
            }
        )
    return rows


def render_sidebar() -> str:
    st.sidebar.title("产品门面")
    view = st.sidebar.radio("视图切换", options=[VIEW_USER, VIEW_ADMIN])
    st.sidebar.caption("展示页面直接调用本地核心模块，适合演示与答辩。")

    sample_cases = case_store.list_samples()
    sample_options = {"手动输入": None}
    sample_options.update({f'{item["case_id"]} | {item["title"]}': item for item in sample_cases})

    st.sidebar.divider()
    st.sidebar.subheader("演示案例")
    selected_label = st.sidebar.selectbox("快速载入样例", options=list(sample_options.keys()), key="sample_choice")
    if st.sidebar.button("载入案例", use_container_width=True) and sample_options[selected_label]:
        load_sample_into_state(sample_options[selected_label])
        st.sidebar.success("样例已载入输入区。")

    st.sidebar.divider()
    st.sidebar.metric("后台案件总数", len(case_store.get_all_cases()))
    return view


def render_user_view() -> None:
    render_page_hero(
        "农民工维权入口",
        "操作保持简洁，重点信息放大显示。输入案情后即可完成分析、文书生成与后台提交。",
        ["大字高亮", "一步式操作", "按钮清晰"],
    )

    left_col, right_col = st.columns([1.1, 1])

    with left_col:
        section_intro("填写案件信息", "保留核心输入项，减少干扰，先说清案情再执行操作。")
        st.text_input("案件标题（可选）", key="case_title", placeholder="例如：工地欠薪三个月")
        st.text_area(
            "案情描述",
            key="case_description",
            height=280,
            placeholder="请输入完整案情，例如：老板拖欠我三个月工资，一共两万四，有微信聊天记录和考勤照片。",
        )
        st.text_area(
            "已有证据（每行一项，可选）",
            key="evidence_text",
            height=150,
            placeholder="身份证明\n聊天记录\n考勤记录或工作记录",
        )
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

    description = st.session_state["case_description"].strip()
    evidence_items = [line.strip() for line in st.session_state["evidence_text"].splitlines() if line.strip()]

    action_report: dict[str, Any] | None = None
    if analyze_clicked or generate_clicked or submit_clicked:
        if not description:
            st.warning("请先输入案情描述。")
        else:
            try:
                facts = parse_facts(st.session_state["facts_json"])
            except (json.JSONDecodeError, ValueError) as exc:
                st.error(f"补充事实格式错误：{exc}")
            else:
                action_report = build_analysis(description, evidence_items, facts)
                st.session_state["analysis_report"] = action_report
                if generate_clicked:
                    st.session_state["generated_document"] = build_document(
                        action_report,
                        st.session_state["selected_template"],
                        facts,
                    )
                if submit_clicked:
                    st.session_state["last_submission"] = case_store.submit_case(
                        description=description,
                        provided_evidence=evidence_items,
                        facts=facts,
                        title=st.session_state["case_title"].strip() or None,
                    )

    analysis_report = st.session_state.get("analysis_report")
    generated_document = st.session_state.get("generated_document")
    last_submission = st.session_state.get("last_submission")

    with right_col:
        section_intro("结果展示区", "分析结论、重点指标和文书预览统一放在右侧，便于答辩时快速说明。")
        if last_submission:
            st.success(
                f"案件已进入检察后台：{last_submission['submission_id']} | "
                f"{last_submission['risk_assessment']['priority_label']}"
            )

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

        st.write("**文书预览**")
        if generated_document:
            st.code(generated_document["document_text"], language="text")
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


def render_admin_view() -> None:
    render_page_hero(
        "检察院决策后台",
        "采用更醒目的数据指标和更克制的页面结构，便于快速查看重点案件与风险分布。",
        ["数据更聚焦", "高亮指标", "简洁筛选"],
    )

    all_cases = case_store.get_all_cases()
    rows = build_case_rows(all_cases)

    if not rows:
        st.info("当前还没有提交案件。")
        return

    section_intro("案件概览", "保留关键筛选和统计信息，减少页面装饰性干扰。")
    threshold = st.slider("证据分数阈值（展示 > 当前值的重点案件）", min_value=0, max_value=100, value=80)
    filtered_rows = [row for row in rows if row["证据分数"] > threshold]

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("案件总数", len(rows))
    metric_col2.metric(f"证据分数 > {threshold}", len(filtered_rows))
    metric_col3.metric("高优先级案件", sum(1 for row in rows if row["优先级"] == "高证据优先关注"))

    st.write("**案件汇总表**")
    st.dataframe(filtered_rows or rows, use_container_width=True, hide_index=True)

    chart_source = filtered_rows or rows
    risk_counts = Counter(row["风险等级"] for row in chart_source)
    chart_data = [
        {"风险等级": level, "案件数量": risk_counts.get(level, 0)}
        for level in ["高风险", "中风险", "低风险"]
        if risk_counts.get(level, 0) > 0
    ]

    st.write("**风险等级分布**")
    if chart_data:
        st.bar_chart(chart_data, x="风险等级", y="案件数量")
    else:
        st.info("当前筛选条件下没有可展示的风险分布数据。")


def main() -> None:
    st.set_page_config(page_title="农民工权益保障智能平台", layout="wide")
    restore_state_from_query_params()
    init_state()
    render_global_styles()

    st.title("农民工权益保障智能平台")
    st.caption("页面风格已调整为简洁、大字、高亮重点，更适合演示场景。")

    view = render_sidebar()
    if view == VIEW_USER:
        render_user_view()
    else:
        render_admin_view()
    persist_state_to_query_params()


if __name__ == "__main__":
    main()
