from __future__ import annotations

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
    st.sidebar.caption("页面直接调用本地 DataProcessor、DocumentGenerator、CaseStore。")

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
    st.subheader("农民工维权入口")
    st.caption("输入案情后直接触发规则引擎分析、结构化抽取和文书生成。")

    left_col, right_col = st.columns([1.1, 1])

    with left_col:
        st.text_input("案件标题（可选）", key="case_title", placeholder="例如：工地欠薪三个月")
        st.text_area(
            "案情描述",
            key="case_description",
            height=240,
            placeholder="请输入完整案情，例如：老板拖欠我三个月工资，一共两万四，有微信聊天记录和考勤照片。",
        )
        st.text_area(
            "已有证据（每行一项，可选）",
            key="evidence_text",
            height=140,
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
    st.subheader("检察院决策后台")
    st.caption("基于 CaseStore 的内存案件池做汇总、筛选和风险分布展示。")

    all_cases = case_store.get_all_cases()
    rows = build_case_rows(all_cases)

    if not rows:
        st.info("当前还没有提交案件。")
        return

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
    init_state()

    st.title("农民工权益保障智能平台")
    st.caption("面向队友和评委演示的 Streamlit 门面，直接联动本地后端核心模块。")

    view = render_sidebar()
    if view == VIEW_USER:
        render_user_view()
    else:
        render_admin_view()


if __name__ == "__main__":
    main()
