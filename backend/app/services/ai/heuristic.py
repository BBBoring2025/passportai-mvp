"""Heuristic (keyword-based) document classifier — cost-free, runs first."""

from __future__ import annotations

from app.services.ai.base import AIService, ClassificationResult

# Keywords for each document type, ordered by specificity
KEYWORD_MAP: dict[str, list[str]] = {
    "invoice": [
        "commercial invoice",
        "proforma invoice",
        "invoice",
        "fatura",
        "ticari fatura",
    ],
    "packing_list": [
        "packing list",
        "ambalaj listesi",
        "packing",
    ],
    "certificate": [
        "oeko-tex",
        "oekotex",
        "oeko tex",
        "gots certificate",
        "certificate",
        "sertifika",
        "iso 9001",
        "iso 14001",
    ],
    "test_report": [
        "test report",
        "test raporu",
        "laboratory report",
        "sgs",
        "bureau veritas",
        "intertek",
        "tuv",
    ],
    "sds": [
        "safety data sheet",
        "guvenlik bilgi formu",
        "material safety data",
        "msds",
        "sds",
    ],
    "bom": [
        "bill of material",
        "material declaration",
        "malzeme bildirimi",
        "bom",
    ],
}

# Confidence levels
FILENAME_CONFIDENCE = 0.85
TEXT_CONFIDENCE = 0.90


class HeuristicClassifier(AIService):
    """Classifies documents using keyword matching on filename and first-page text."""

    def classify(self, filename: str, first_page_text: str) -> ClassificationResult | None:
        fn_lower = filename.lower()
        text_lower = first_page_text.lower()

        # Score each doc_type
        best_type: str | None = None
        best_score = 0
        best_confidence = 0.0

        for doc_type, keywords in KEYWORD_MAP.items():
            score = 0
            source_confidence = 0.0

            # Check filename
            for kw in keywords:
                if kw in fn_lower:
                    score += 2  # filename match is weighted
                    source_confidence = max(source_confidence, FILENAME_CONFIDENCE)

            # Check first page text
            for kw in keywords:
                if kw in text_lower:
                    score += 1
                    source_confidence = max(source_confidence, TEXT_CONFIDENCE)

            if score > best_score:
                best_score = score
                best_type = doc_type
                best_confidence = source_confidence

        if best_type is None or best_score == 0:
            return None  # uncertain — needs LLM fallback

        return ClassificationResult(
            doc_type=best_type,
            confidence=best_confidence,
            method="heuristic",
        )
