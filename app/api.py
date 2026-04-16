from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.service import (
    analyze_case,
    ask_question,
    generate_document,
    get_case_detail,
    get_prosecutor_dashboard,
    list_sample_cases,
    list_submitted_cases,
    review_case,
    submit_case,
    submit_sample_case,
    update_case_facts,
)


app = FastAPI(
    title="农民工权益保障智能平台",
    version="0.2.0",
    description="基于 Mock Data、规则引擎和 Jinja2 模板的 FastAPI 演示后端。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    description: str = Field(..., description="农民工提交的原始案情文本")
    provided_evidence: list[str] = Field(default_factory=list, description="已有证据清单")
    facts: dict[str, Any] = Field(default_factory=dict, description="表单补充信息")
    user_profile: dict[str, Any] = Field(default_factory=dict, description="劳动者基础信息")
    dispute_profile: dict[str, Any] = Field(default_factory=dict, description="欠薪线索与争议信息")
    evidence_catalog: dict[str, list[str]] = Field(default_factory=dict, description="证据分类清单")


class SubmitCaseRequest(BaseModel):
    title: str | None = Field(default=None, description="案件标题")
    description: str = Field(..., description="案情描述")
    provided_evidence: list[str] = Field(default_factory=list, description="已有证据清单")
    facts: dict[str, Any] = Field(default_factory=dict, description="补充事实字段")
    user_profile: dict[str, Any] = Field(default_factory=dict, description="劳动者基础信息")
    dispute_profile: dict[str, Any] = Field(default_factory=dict, description="欠薪线索与争议信息")
    evidence_catalog: dict[str, list[str]] = Field(default_factory=dict, description="证据分类清单")


class QuestionRequest(BaseModel):
    question: str


class DocumentRequest(BaseModel):
    template_name: str = Field(
        ...,
        pattern="^(arbitration_application|support_prosecution_application|civil_complaint_non_construction|civil_complaint_construction|support_prosecution_opinion_non_construction|support_prosecution_opinion_construction)$",
    )
    description: str
    provided_evidence: list[str] = Field(default_factory=list)
    facts: dict[str, Any] = Field(default_factory=dict)


class ReviewRequest(BaseModel):
    case_status: str
    mediation_priority: str = Field(default="待评估")
    prosecution_necessity: str = Field(default="待评估")
    prosecutor_note: str = Field(default="")
    user_message: str = Field(default="")
    relief_checks: dict[str, bool] = Field(default_factory=dict)
    relief_note: str = Field(default="")
    mediation_case_type: str = Field(default="")
    prosecution_case_type: str = Field(default="")


class FactsPatchRequest(BaseModel):
    facts_patch: dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, object]:
    return {
        "name": "农民工权益保障智能平台",
        "version": "0.2.0",
        "docs": "/docs",
        "workflow": [
            "案情文本清洗结构化",
            "规则引擎风险评估",
            "文书自动生成",
            "检察院 dashboard 汇总研判",
        ],
    }


@app.get("/capabilities")
def capabilities() -> dict[str, object]:
    return {
        "backend": "FastAPI",
        "data_mode": "Mock Data + In-Memory Store",
        "modules": [
            "DataProcessor: 文本清洗与法律辅助",
            "DocumentGenerator: Jinja2 文书生成",
            "CaseStore: 提交案件与检察院汇总",
        ],
        "document_templates": [
            {"key": "arbitration_application", "label": "劳动仲裁申请书"},
            {"key": "support_prosecution_application", "label": "支持起诉申请书"},
            {"key": "civil_complaint_non_construction", "label": "民事起诉状（非工程建设领域）"},
            {"key": "civil_complaint_construction", "label": "民事起诉状（工程建设领域）"},
            {"key": "support_prosecution_opinion_non_construction", "label": "支持起诉书（非工程建设领域）"},
            {"key": "support_prosecution_opinion_construction", "label": "支持起诉书（工程建设领域）"},
        ],
        "supported_scenarios": ["欠薪", "工伤", "未签劳动合同"],
    }


@app.get("/cases/samples")
def get_sample_cases() -> dict[str, list[dict[str, Any]]]:
    return {"items": list_sample_cases()}


@app.get("/cases/submissions")
def get_submitted_cases() -> dict[str, list[dict[str, Any]]]:
    return {"items": list_submitted_cases()}


@app.get("/cases/{submission_id}")
def get_case(submission_id: str) -> dict[str, Any]:
    try:
        return get_case_detail(submission_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found") from exc


@app.post("/case/analyze")
def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
    return analyze_case(payload.description, payload.provided_evidence, payload.facts)


@app.post("/cases/submit")
def create_submission(payload: SubmitCaseRequest) -> dict[str, Any]:
    return submit_case(
        description=payload.description,
        provided_evidence=payload.provided_evidence,
        facts=payload.facts,
        title=payload.title,
        user_profile=payload.user_profile,
        dispute_profile=payload.dispute_profile,
        evidence_catalog=payload.evidence_catalog,
    )


@app.post("/cases/submit/sample/{case_id}")
def create_sample_submission(case_id: str) -> dict[str, Any]:
    try:
        return submit_sample_case(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Sample case {case_id} not found") from exc


@app.post("/cases/{submission_id}/review")
def submit_review(submission_id: str, payload: ReviewRequest) -> dict[str, Any]:
    try:
        return review_case(
            submission_id=submission_id,
            case_status=payload.case_status,
            mediation_priority=payload.mediation_priority,
            prosecution_necessity=payload.prosecution_necessity,
            prosecutor_note=payload.prosecutor_note,
            user_message=payload.user_message,
            relief_checks=payload.relief_checks,
            relief_note=payload.relief_note,
            mediation_case_type=payload.mediation_case_type,
            prosecution_case_type=payload.prosecution_case_type,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found") from exc


@app.post("/cases/{submission_id}/facts")
def patch_case_facts(submission_id: str, payload: FactsPatchRequest) -> dict[str, Any]:
    try:
        return update_case_facts(submission_id, payload.facts_patch)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found") from exc


@app.post("/qa/answer")
def qa_answer(payload: QuestionRequest) -> dict[str, object]:
    return ask_question(payload.question)


@app.post("/document/generate")
def document_generate(payload: DocumentRequest) -> dict[str, Any]:
    return generate_document(
        payload.template_name,
        payload.description,
        payload.facts,
        payload.provided_evidence,
    )


@app.get("/prosecutor/dashboard")
def prosecutor_dashboard() -> dict[str, Any]:
    return get_prosecutor_dashboard()
