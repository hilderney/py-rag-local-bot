from dataclasses import dataclass
from pathlib import Path
from typing import Literal

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
    stage: Literal["extract", "summarize", "info", "error", "done"]
    filename: str
    message: str


@dataclass
class PipelineStats:
    pdfs_found: int = 0
    extracted: int = 0
    summarized: int = 0
    skipped: int = 0
    failed: int = 0


@dataclass
class SummaryResult:
    modelo: str
    requisicao: str | dict
    resposta: dict


@dataclass
class SummarizeOutcome:
    result: SummaryResult
    truncated: bool = False


DEFAULT_OLLAMA_MODEL = "gemma3:270m"
DEFAULT_OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
DEFAULT_MAX_CHARS_OLLAMA = 8000
DEFAULT_MAX_CHARS_OPENROUTER = 10000
