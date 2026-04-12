from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.service import (
    analyze_case,
    ask_question,
    generate_document,
    get_prosecutor_dashboard,
    list_sample_cases,
    list_submitted_cases,
    submit_case,
    submit_sample_case,
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


class SubmitCaseRequest(BaseModel):
    title: str | None = Field(default=None, description="案件标题")
    description: str = Field(..., description="案情描述")
    provided_evidence: list[str] = Field(default_factory=list, description="已有证据清单")
    facts: dict[str, Any] = Field(default_factory=dict, description="补充事实字段")


class QuestionRequest(BaseModel):
    question: str


class DocumentRequest(BaseModel):
    template_name: str = Field(..., pattern="^(arbitration_application|support_prosecution_application)$")
    description: str
    provided_evidence: list[str] = Field(default_factory=list)
    facts: dict[str, Any] = Field(default_factory=dict)


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
        ],
        "supported_scenarios": ["欠薪", "工伤", "未签劳动合同"],
    }


@app.get("/cases/samples")
def get_sample_cases() -> dict[str, list[dict[str, Any]]]:
    return {"items": list_sample_cases()}


@app.get("/cases/submissions")
def get_submitted_cases() -> dict[str, list[dict[str, Any]]]:
    return {"items": list_submitted_cases()}


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
    )


@app.post("/cases/submit/sample/{case_id}")
def create_sample_submission(case_id: str) -> dict[str, Any]:
    try:
        return submit_sample_case(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Sample case {case_id} not found") from exc


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
