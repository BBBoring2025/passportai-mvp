"""
Claude-powered field extraction — page-by-page for cost optimization.

Contract:
- Extract ONLY values that exist in the document text.
- Do NOT generate, estimate, or infer values not present.
- No snippet = no value. Every field MUST have evidence.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field

from app.services.ai.field_mapping import DOC_TYPE_FIELDS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a document data extraction engine for \
textile trade documents.
Extract ONLY values that exist in the document text.
Do NOT generate, estimate, or infer values not present.
Return a JSON array of extracted fields."""

MAX_PAGE_CHARS = 8000


@dataclass
class ExtractionResult:
    """Single extracted field with evidence."""

    canonical_key: str
    value: str
    unit: str | None
    page: int
    snippet: str
    confidence: float


@dataclass
class ExtractionUsage:
    """Token usage tracking across all pages."""

    input_tokens: int = 0
    output_tokens: int = 0
    pages_processed: int = 0
    pages_skipped: int = 0


@dataclass
class ExtractionOutput:
    """Full extraction output."""

    results: list[ExtractionResult] = field(default_factory=list)
    usage: ExtractionUsage = field(default_factory=ExtractionUsage)


def _build_user_prompt(
    doc_type: str, page_no: int, page_text: str, keys: list[str]
) -> str:
    truncated = page_text[:MAX_PAGE_CHARS]
    keys_str = ", ".join(keys)
    return (
        f"Document type: {doc_type}. Page {page_no} text:\n"
        f'"""{truncated}"""\n\n'
        f"Extract these fields: {keys_str}.\n"
        f"For each field found, return:\n"
        f'{{ "canonical_key": "...", "value": "...", '
        f'"unit": "...", "confidence": 0.0-1.0, '
        f'"page_no": {page_no}, '
        f'"snippet_text": "exact quote from document, '
        f'max 200 chars" }}.\n\n'
        f"If a field is not found on this page, "
        f"omit it from the result.\n"
        f"Return ONLY valid JSON array, no markdown, "
        f"no explanation."
    )


def _parse_results(
    raw_text: str,
    doc_type: str,
    page_no: int,
    valid_keys: set[str],
) -> list[ExtractionResult]:
    """Parse Claude's JSON response into ExtractionResult list."""
    # Strip markdown fences if present
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (fences)
        lines = [
            ln
            for ln in lines
            if not ln.strip().startswith("```")
        ]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(
            "Malformed JSON from Claude on page %d: %.100s",
            page_no,
            text,
        )
        return []

    if not isinstance(data, list):
        data = [data]

    results: list[ExtractionResult] = []
    for item in data:
        if not isinstance(item, dict):
            continue

        key = item.get("canonical_key", "")
        value = str(item.get("value", "")).strip()
        snippet = str(item.get("snippet_text", "")).strip()

        # Validation: key must be valid, value and snippet required
        if key not in valid_keys:
            logger.debug(
                "Discarding invalid key '%s' for %s", key, doc_type
            )
            continue
        if not value:
            logger.debug("Discarding empty value for key '%s'", key)
            continue
        if not snippet:
            logger.debug(
                "Discarding key '%s' — no snippet (no evidence)",
                key,
            )
            continue

        confidence = float(item.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        unit = item.get("unit")
        if unit is not None:
            unit = str(unit).strip() or None

        results.append(
            ExtractionResult(
                canonical_key=key,
                value=value,
                unit=unit,
                page=item.get("page_no", page_no),
                snippet=snippet[:200],
                confidence=confidence,
            )
        )

    return results


def _deduplicate(
    results: list[ExtractionResult],
) -> list[ExtractionResult]:
    """Keep highest-confidence result per canonical_key."""
    best: dict[str, ExtractionResult] = {}
    for r in results:
        existing = best.get(r.canonical_key)
        if existing is None or r.confidence > existing.confidence:
            best[r.canonical_key] = r
    return list(best.values())


def snippet_hash(text: str) -> str:
    """SHA256 hash of snippet text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ClaudeExtractor:
    """Extracts fields from document pages using Claude API."""

    def __init__(self, api_key: str):
        self._api_key = api_key

    def extract_fields(
        self,
        doc_type: str,
        pages: list[tuple[int, str]],
    ) -> ExtractionOutput:
        """
        Extract fields from document pages.

        Args:
            doc_type: Classification (invoice, bom, etc.)
            pages: List of (page_number, page_text) tuples.

        Returns:
            ExtractionOutput with deduplicated results and
            token usage metadata.
        """
        import anthropic

        valid_keys_list = DOC_TYPE_FIELDS.get(doc_type, [])
        if not valid_keys_list:
            logger.warning("No field mapping for doc_type: %s", doc_type)
            return ExtractionOutput()

        valid_keys = set(valid_keys_list)
        client = anthropic.Anthropic(api_key=self._api_key)

        all_results: list[ExtractionResult] = []
        usage = ExtractionUsage()

        for page_no, page_text in pages:
            if not page_text or not page_text.strip():
                usage.pages_skipped += 1
                continue

            user_prompt = _build_user_prompt(
                doc_type, page_no, page_text, valid_keys_list
            )

            try:
                message = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=2048,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ],
                )

                usage.input_tokens += message.usage.input_tokens
                usage.output_tokens += message.usage.output_tokens
                usage.pages_processed += 1

                response_text = message.content[0].text
                page_results = _parse_results(
                    response_text, doc_type, page_no, valid_keys
                )
                all_results.extend(page_results)

            except Exception as exc:
                logger.error(
                    "Claude extraction failed on page %d: %s",
                    page_no,
                    exc,
                )
                usage.pages_skipped += 1
                continue

        # Deduplicate: same key on multiple pages → highest confidence
        deduplicated = _deduplicate(all_results)

        return ExtractionOutput(results=deduplicated, usage=usage)
