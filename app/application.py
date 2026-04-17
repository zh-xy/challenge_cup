from __future__ import annotations

from dataclasses import dataclass

from app.case_store import CaseStore
from app.data_processor import DataProcessor
from app.document_generator import DocumentGenerator
from app.llm_client import LLMClient
from core.knowledge_base import KnowledgeBase


@dataclass(slots=True)
class ApplicationServices:
    kb: KnowledgeBase
    data_processor: DataProcessor
    document_generator: DocumentGenerator
    case_store: CaseStore
    llm_client: LLMClient


def build_application() -> ApplicationServices:
    kb = KnowledgeBase()
    data_processor = DataProcessor(kb)
    return ApplicationServices(
        kb=kb,
        data_processor=data_processor,
        document_generator=DocumentGenerator(),
        case_store=CaseStore(kb, data_processor),
        llm_client=LLMClient(),
    )
