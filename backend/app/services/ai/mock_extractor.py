"""
Mock extractor for testing — returns hardcoded results
matching golden_set_ground_truth.csv.

Usage: when ANTHROPIC_API_KEY is unavailable or network
is unreachable, the factory returns MockExtractor instead.
All results are clearly tagged with created_from="mock".

This lets us verify the FULL pipeline (field storage,
evidence anchors, API responses, frontend) without API costs.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

from app.services.ai.extractor import (
    ExtractionOutput,
    ExtractionResult,
    ExtractionUsage,
)

logger = logging.getLogger(__name__)

GROUND_TRUTH_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "sample_docs"
    / "golden_set_ground_truth.csv"
)

# Filename stem → doc_id mapping
FILENAME_TO_DOC_ID: dict[str, str] = {
    "01_commercial_invoice.pdf": "01_commercial_invoice",
    "02_packing_list.pdf": "02_packing_list",
    "03_oekotex_certificate.pdf": "03_oekotex_certificate",
    "04_test_report_sgs.pdf": "04_test_report_sgs",
    "05_sds_reactive_dye.pdf": "05_sds_reactive_dye",
    "06_bom_material_declaration.pdf": "06_bom_material_declaration",
}


@dataclass
class GroundTruthEntry:
    doc_id: str
    doc_type: str
    canonical_key: str
    expected_value: str
    expected_unit: str
    expected_page: int
    expected_snippet_contains: str


def _load_ground_truth() -> dict[str, list[GroundTruthEntry]]:
    """Load and group ground truth by doc_type."""
    if not GROUND_TRUTH_PATH.exists():
        logger.warning(
            "Ground truth CSV not found: %s",
            GROUND_TRUTH_PATH,
        )
        return {}

    by_type: dict[str, list[GroundTruthEntry]] = {}
    with open(GROUND_TRUTH_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry = GroundTruthEntry(
                doc_id=row["doc_id"],
                doc_type=row["doc_type"],
                canonical_key=row["canonical_key"],
                expected_value=row["expected_value"],
                expected_unit=row.get("expected_unit", ""),
                expected_page=int(
                    row.get("expected_page", "1") or "1"
                ),
                expected_snippet_contains=row.get(
                    "expected_snippet_contains", ""
                ),
            )
            by_type.setdefault(entry.doc_type, []).append(entry)

    return by_type


# Pre-load at module level
_GROUND_TRUTH = _load_ground_truth()


class MockExtractor:
    """
    Returns hardcoded extraction results from ground truth CSV.

    Matches doc_type to find expected fields, then generates
    mock snippets using the expected_snippet_contains value.
    """

    def extract_fields(
        self,
        doc_type: str,
        pages: list[tuple[int, str]],
    ) -> ExtractionOutput:
        gt_entries = _GROUND_TRUTH.get(doc_type, [])
        if not gt_entries:
            logger.warning(
                "MockExtractor: no ground truth for doc_type=%s",
                doc_type,
            )
            return ExtractionOutput()

        # Build page text lookup for snippet matching
        page_texts = {pn: text for pn, text in pages}

        results: list[ExtractionResult] = []
        for entry in gt_entries:
            # Try to find the snippet in actual page text
            page_text = page_texts.get(entry.expected_page, "")
            snippet = entry.expected_snippet_contains
            if snippet and page_text:
                # Find snippet in context (up to 200 chars around it)
                idx = page_text.find(snippet)
                if idx >= 0:
                    start = max(0, idx - 20)
                    end = min(len(page_text), idx + len(snippet) + 20)
                    snippet = page_text[start:end].strip()
                else:
                    # Use the expected snippet as-is
                    snippet = entry.expected_snippet_contains
            elif not snippet:
                snippet = f"[mock] {entry.canonical_key}"

            results.append(
                ExtractionResult(
                    canonical_key=entry.canonical_key,
                    value=entry.expected_value,
                    unit=entry.expected_unit or None,
                    page=entry.expected_page,
                    snippet=snippet[:200],
                    confidence=0.95,
                )
            )

        usage = ExtractionUsage(
            input_tokens=0,
            output_tokens=0,
            pages_processed=len(pages),
            pages_skipped=0,
        )

        logger.info(
            "MockExtractor: returned %d fields for %s",
            len(results),
            doc_type,
        )
        return ExtractionOutput(results=results, usage=usage)
