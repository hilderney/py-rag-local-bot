from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pdf_summarizer.core.summary.schema import DEFAULT_USER_PROMPT


@dataclass
class JobConfig:
    input_dir: Path
    output_dir: Path
    provider: Literal["ollama", "openrouter"]
    model: str
    api_key: str | None = None
    max_chars: int = 8000
    user_prompt: str = DEFAULT_USER_PROMPT


@dataclass
class ProgressEvent:
    stage: Literal["extract", "table", "summarize", "info", "error", "done"]
    filename: str
    message: str


@dataclass
class ExtractStats:
    pdfs_found: int = 0
    extracted: int = 0
    failed: int = 0


@dataclass
class TableStats:
    files_found: int = 0
    tables_extracted: int = 0
    skipped: int = 0
    failed: int = 0


@dataclass
class LlmStats:
    files_found: int = 0
    processed: int = 0
    skipped: int = 0
    failed: int = 0


@dataclass
class LlmResponse:
    """Resposta parseada da LLM ({resposta, resumo})."""

    resposta: str
    resumo: str


@dataclass
class ProviderResult:
    """Resultado bruto do provider antes de montar o documento final."""

    modelo: str
    provedor: Literal["ollama", "openrouter"]
    requisicao: str | dict
    llm_response: LlmResponse


@dataclass
class LlmDocument:
    """Documento JSON salvo em respostas/*.json."""

    modelo: str
    provedor: str
    texto: str
    requisitado: str
    resposta: str
    resumo: str
    arquivos: dict[str, str | None] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "modelo": self.modelo,
            "provedor": self.provedor,
            "texto": self.texto,
            "requisitado": self.requisitado,
            "resposta": self.resposta,
            "resumo": self.resumo,
            "arquivos": self.arquivos,
        }


@dataclass
class LlmOutcome:
    document: LlmDocument
    truncated: bool = False


DEFAULT_OLLAMA_MODEL = "gemma3:270m"
DEFAULT_OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
DEFAULT_MAX_CHARS_OLLAMA = 8000
DEFAULT_MAX_CHARS_OPENROUTER = 10000
