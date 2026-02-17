"""AI service factory — classifiers and extractors."""

from __future__ import annotations

from app.config import settings
from app.services.ai.base import AIService
from app.services.ai.heuristic import HeuristicClassifier


def get_classifier() -> AIService:
    """
    Returns the best available classifier.

    - Always includes HeuristicClassifier (zero cost).
    - If anthropic_api_key is configured, wraps with CompositeClassifier
      so LLM is used only when heuristic is uncertain.
    """
    heuristic = HeuristicClassifier()

    if settings.anthropic_api_key:
        from app.services.ai.claude import ClaudeClassifier
        from app.services.ai.composite import CompositeClassifier

        llm = ClaudeClassifier(api_key=settings.anthropic_api_key)
        return CompositeClassifier(heuristic=heuristic, llm=llm)

    return heuristic


def get_extractor(use_mock: bool = False):
    """
    Returns an extractor instance.

    - use_mock=True → MockExtractor (ground truth, for testing)
    - use_mock=False + API key → ClaudeExtractor (real AI)
    - use_mock=False + no key → None (caller should 503)
    """
    if use_mock:
        from app.services.ai.mock_extractor import MockExtractor

        return MockExtractor()

    if not settings.anthropic_api_key:
        return None

    from app.services.ai.extractor import ClaudeExtractor

    return ClaudeExtractor(api_key=settings.anthropic_api_key)
