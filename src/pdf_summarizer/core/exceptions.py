class PdfSummarizerError(Exception):
    """Base exception for PDF Summarizer."""


class PdfExtractError(PdfSummarizerError):
    """Raised when PDF extraction fails."""


class LlmError(PdfSummarizerError):
    """Raised when LLM communication fails."""


class LlmParseError(LlmError):
    """Raised when LLM response cannot be parsed or validated."""


class ConfigError(PdfSummarizerError):
    """Raised when configuration is invalid."""
