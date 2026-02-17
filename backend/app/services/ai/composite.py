"""Composite classifier — heuristic first, LLM fallback if uncertain."""

from __future__ import annotations

from app.services.ai.base import AIService, ClassificationResult

# Minimum heuristic confidence to skip LLM
HEURISTIC_CONFIDENCE_THRESHOLD = 0.80


class CompositeClassifier(AIService):
    """Runs heuristic classification first, falls back to LLM if uncertain."""

    def __init__(self, heuristic: AIService, llm: AIService):
        self._heuristic = heuristic
        self._llm = llm

    def classify(self, filename: str, first_page_text: str) -> ClassificationResult | None:
        # Step 1: Try heuristic
        result = self._heuristic.classify(filename, first_page_text)

        if result and result.confidence >= HEURISTIC_CONFIDENCE_THRESHOLD:
            return result  # confident enough, skip LLM

        # Step 2: Try LLM
        llm_result = self._llm.classify(filename, first_page_text)
        if llm_result:
            return llm_result

        # Step 3: Fall back to heuristic result even if low confidence
        return result
