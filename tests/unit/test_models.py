from pdf_summarizer.core.exceptions import (
    ConfigError,
    LlmError,
    LlmParseError,
    PdfExtractError,
    PdfSummarizerError,
)
from pdf_summarizer.core.models import JobConfig, PipelineStats, ProgressEvent, SummaryResult


def test_job_config_defaults():
    from pathlib import Path

    config = JobConfig(
        input_dir=Path("in"),
        output_dir=Path("out"),
        provider="ollama",
        model="gemma3:270m",
    )
    assert config.max_chars == 8000
    assert config.api_key is None


def test_progress_event():
    event = ProgressEvent(stage="extract", filename="a.pdf", message="msg")
    assert event.stage == "extract"


def test_pipeline_stats_defaults():
    stats = PipelineStats()
    assert stats.pdfs_found == 0


def test_exceptions_hierarchy():
    assert issubclass(PdfExtractError, PdfSummarizerError)
    assert issubclass(LlmParseError, LlmError)
    assert issubclass(ConfigError, PdfSummarizerError)
