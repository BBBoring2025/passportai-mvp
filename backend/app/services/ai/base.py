"""Abstract base for AI classification services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

# Valid document types
VALID_DOC_TYPES = frozenset(
    {"invoice", "packing_list", "certificate", "test_report", "sds", "bom"}
)


@dataclass
class ClassificationResult:
    """Result of document classification."""

    doc_type: str  # invoice | packing_list | certificate | test_report | sds | bom
    confidence: float  # 0.0 - 1.0
    method: str  # "heuristic" | "llm"


class AIService(ABC):
    """Abstract base class for document classification."""

    @abstractmethod
    def classify(self, filename: str, first_page_text: str) -> ClassificationResult | None:
        """
        Classify a document based on filename and first page text.

        Returns ClassificationResult if classification is possible, None if uncertain.
        """
        ...
