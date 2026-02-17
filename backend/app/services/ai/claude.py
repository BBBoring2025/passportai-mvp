"""Claude LLM classifier — fallback when heuristic is uncertain."""

from __future__ import annotations

import json
import logging

from app.services.ai.base import VALID_DOC_TYPES, AIService, ClassificationResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a document classifier for textile supply chain documents.

Classify the document into exactly one of these types:
- invoice (commercial invoice, proforma invoice)
- packing_list (packing list, shipment list)
- certificate (OEKO-TEX, GOTS, ISO certificates)
- test_report (SGS, Bureau Veritas, Intertek lab reports)
- sds (Safety Data Sheet, MSDS)
- bom (Bill of Materials, material declaration)

Respond with ONLY valid JSON:
{"doc_type": "<type>", "confidence": <0.0-1.0>}

Do not include any other text."""

MAX_TEXT_CHARS = 2000


class ClaudeClassifier(AIService):
    """Classifies documents using Claude API."""

    def __init__(self, api_key: str):
        self._api_key = api_key

    def classify(self, filename: str, first_page_text: str) -> ClassificationResult | None:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self._api_key)

            user_prompt = (
                f"Filename: {filename}\n\n"
                f"First page text (truncated):\n{first_page_text[:MAX_TEXT_CHARS]}"
            )

            message = client.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=100,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Parse response
            response_text = message.content[0].text.strip()
            data = json.loads(response_text)

            doc_type = data.get("doc_type", "")
            confidence = float(data.get("confidence", 0.0))

            if doc_type not in VALID_DOC_TYPES:
                logger.warning("Claude returned invalid doc_type: %s", doc_type)
                return None

            return ClassificationResult(
                doc_type=doc_type,
                confidence=min(confidence, 1.0),
                method="llm",
            )

        except Exception as exc:
            logger.warning("Claude classification failed: %s", exc)
            return None
