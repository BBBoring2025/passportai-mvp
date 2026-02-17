#!/usr/bin/env python3
"""
Evaluation harness for Sprint 3 field extraction.

Usage:
    cd passportai
    python -m eval.run_eval

Reads 6 sample PDFs, extracts text, classifies, then runs
AI field extraction via ClaudeExtractor. Compares results
against golden_set_ground_truth.csv.

Outputs: eval/accuracy_report.json + console summary table.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# Add backend to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.services.ai.extractor import ClaudeExtractor  # noqa: E402
from app.services.ai.heuristic import (  # noqa: E402
    HeuristicClassifier,
)
from app.services.extraction import extract_text  # noqa: E402

SAMPLE_DIR = ROOT / "sample_docs"
GROUND_TRUTH = SAMPLE_DIR / "golden_set_ground_truth.csv"
OUTPUT_DIR = ROOT / "eval"


@dataclass
class GroundTruthRow:
    doc_id: str
    doc_type: str
    canonical_key: str
    expected_value: str
    expected_unit: str
    expected_page: int
    expected_snippet_contains: str


@dataclass
class EvalResult:
    doc_id: str
    canonical_key: str
    expected_value: str
    actual_value: str | None
    match_type: str  # exact_match | normalized_match | numeric_tolerance | miss
    snippet_found: bool
    details: str


def load_ground_truth() -> list[GroundTruthRow]:
    """Load ground truth CSV."""
    rows: list[GroundTruthRow] = []
    with open(GROUND_TRUTH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                GroundTruthRow(
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
            )
    return rows


def normalize_date(value: str) -> str:
    """Try to normalize various date formats to YYYY-MM-DD."""
    # Already in YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value

    # Try DD Month YYYY
    import datetime

    formats = [
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(value.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return value


def normalize_number(value: str) -> float | None:
    """Parse number, stripping commas/whitespace."""
    cleaned = value.replace(",", "").replace(" ", "").strip()
    # Remove trailing % or unit
    cleaned = re.sub(r"[%a-zA-Z]+$", "", cleaned)
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_text(value: str) -> str:
    """Strip + lowercase for text comparison."""
    return value.strip().lower()


def compare_values(
    expected: str, actual: str, canonical_key: str
) -> tuple[str, str]:
    """
    Compare expected vs actual value.
    Returns (match_type, details).
    """
    if not actual:
        return ("miss", "No value extracted")

    # Exact match
    if expected.strip() == actual.strip():
        return ("exact_match", "")

    # Date normalization
    if "date" in canonical_key or "valid_until" in canonical_key:
        exp_norm = normalize_date(expected)
        act_norm = normalize_date(actual)
        if exp_norm == act_norm:
            return (
                "normalized_match",
                f"dates: {expected} -> {exp_norm}",
            )

    # Numeric comparison (percentages, quantities)
    exp_num = normalize_number(expected)
    act_num = normalize_number(actual)
    if exp_num is not None and act_num is not None:
        if exp_num == act_num:
            return (
                "normalized_match",
                f"numbers: {expected} == {actual}",
            )
        if abs(exp_num - act_num) <= 1:
            return (
                "numeric_tolerance",
                f"within ±1: {exp_num} vs {act_num}",
            )

    # Text normalization (case insensitive)
    if normalize_text(expected) == normalize_text(actual):
        return (
            "normalized_match",
            f"case-insensitive: '{expected}' == '{actual}'",
        )

    # Partial match (actual contains expected or vice versa)
    if normalize_text(expected) in normalize_text(actual):
        return (
            "normalized_match",
            f"partial: '{expected}' in '{actual}'",
        )
    if normalize_text(actual) in normalize_text(expected):
        return (
            "normalized_match",
            f"partial: '{actual}' in '{expected}'",
        )

    return ("miss", f"mismatch: '{expected}' vs '{actual}'")


def run_eval():
    """Main evaluation loop."""
    from app.config import settings

    if not settings.anthropic_api_key:
        print(
            "ERROR: ANTHROPIC_API_KEY not set. "
            "Cannot run extraction evaluation."
        )
        sys.exit(1)

    ground_truth = load_ground_truth()
    print(f"Loaded {len(ground_truth)} ground truth entries")

    classifier = HeuristicClassifier()
    extractor = ClaudeExtractor(api_key=settings.anthropic_api_key)

    # Group ground truth by doc_id
    gt_by_doc: dict[str, list[GroundTruthRow]] = {}
    for gt in ground_truth:
        gt_by_doc.setdefault(gt.doc_id, []).append(gt)

    all_results: list[EvalResult] = []
    total_tokens = {"input": 0, "output": 0}

    for doc_id, gt_rows in gt_by_doc.items():
        pdf_path = SAMPLE_DIR / f"{doc_id}.pdf"
        if not pdf_path.exists():
            print(f"SKIP: {pdf_path} not found")
            continue

        print(f"\n--- {doc_id} ---")
        file_bytes = pdf_path.read_bytes()

        # Extract text
        try:
            page_texts = extract_text(file_bytes, "application/pdf")
        except Exception as exc:
            print(f"  TEXT EXTRACTION FAILED: {exc}")
            for gt in gt_rows:
                all_results.append(
                    EvalResult(
                        doc_id=doc_id,
                        canonical_key=gt.canonical_key,
                        expected_value=gt.expected_value,
                        actual_value=None,
                        match_type="miss",
                        snippet_found=False,
                        details=f"text extraction failed: {exc}",
                    )
                )
            continue

        # Classify
        first_text = page_texts[0].text if page_texts else ""
        cls_result = classifier.classify(doc_id + ".pdf", first_text)
        doc_type = cls_result.doc_type if cls_result else gt_rows[0].doc_type
        print(f"  Classified as: {doc_type}")

        # Extract fields
        pages = [(pt.page_number, pt.text) for pt in page_texts]
        try:
            output = extractor.extract_fields(doc_type, pages)
        except Exception as exc:
            print(f"  EXTRACTION FAILED: {exc}")
            for gt in gt_rows:
                all_results.append(
                    EvalResult(
                        doc_id=doc_id,
                        canonical_key=gt.canonical_key,
                        expected_value=gt.expected_value,
                        actual_value=None,
                        match_type="miss",
                        snippet_found=False,
                        details=f"extraction failed: {exc}",
                    )
                )
            continue

        total_tokens["input"] += output.usage.input_tokens
        total_tokens["output"] += output.usage.output_tokens
        print(
            f"  Extracted {len(output.results)} fields "
            f"(tokens: {output.usage.input_tokens}i/"
            f"{output.usage.output_tokens}o)"
        )

        # Build result lookup
        extracted_map = {r.canonical_key: r for r in output.results}

        for gt in gt_rows:
            extracted = extracted_map.get(gt.canonical_key)
            actual_value = extracted.value if extracted else None

            match_type, details = compare_values(
                gt.expected_value,
                actual_value or "",
                gt.canonical_key,
            )

            # Check snippet
            snippet_found = False
            if extracted and extracted.snippet:
                if gt.expected_snippet_contains:
                    snippet_found = (
                        gt.expected_snippet_contains.lower()
                        in extracted.snippet.lower()
                    )
                else:
                    snippet_found = bool(extracted.snippet)

            result = EvalResult(
                doc_id=doc_id,
                canonical_key=gt.canonical_key,
                expected_value=gt.expected_value,
                actual_value=actual_value,
                match_type=match_type,
                snippet_found=snippet_found,
                details=details,
            )
            all_results.append(result)

            status_char = {
                "exact_match": "=",
                "normalized_match": "~",
                "numeric_tolerance": "~",
                "miss": "X",
            }.get(match_type, "?")

            snip_char = "S" if snippet_found else "-"

            print(
                f"  [{status_char}][{snip_char}] "
                f"{gt.canonical_key}: "
                f"expected='{gt.expected_value}' "
                f"actual='{actual_value or 'N/A'}'"
            )

    # --- Summary ---
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    total = len(all_results)
    exact = sum(1 for r in all_results if r.match_type == "exact_match")
    normalized = sum(
        1
        for r in all_results
        if r.match_type in ("normalized_match", "numeric_tolerance")
    )
    missed = sum(1 for r in all_results if r.match_type == "miss")
    snippets_found = sum(1 for r in all_results if r.snippet_found)

    accuracy = (exact + normalized) / total * 100 if total else 0
    snippet_rate = snippets_found / total * 100 if total else 0

    print(f"Total fields:        {total}")
    print(f"Exact matches:       {exact}")
    print(f"Normalized matches:  {normalized}")
    print(f"Missed:              {missed}")
    print(f"Accuracy:            {accuracy:.1f}%")
    print(f"Snippet coverage:    {snippets_found}/{total} ({snippet_rate:.1f}%)")
    print(
        f"Total tokens:        "
        f"{total_tokens['input']}i / {total_tokens['output']}o"
    )

    # --- Write report ---
    report = {
        "summary": {
            "total_fields": total,
            "exact_matches": exact,
            "normalized_matches": normalized,
            "missed": missed,
            "accuracy_pct": round(accuracy, 1),
            "snippet_coverage_pct": round(snippet_rate, 1),
            "total_input_tokens": total_tokens["input"],
            "total_output_tokens": total_tokens["output"],
        },
        "results": [asdict(r) for r in all_results],
    }

    report_path = OUTPUT_DIR / "accuracy_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport written to: {report_path}")

    # Exit with non-zero if accuracy < 70%
    if accuracy < 70:
        print(f"\nWARNING: Accuracy {accuracy:.1f}% is below 70% target")
        sys.exit(1)


if __name__ == "__main__":
    run_eval()
