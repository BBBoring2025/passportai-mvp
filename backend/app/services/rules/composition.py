"""Rule: Material composition percentages must sum to 99-101%."""

from __future__ import annotations

from app.services.rules.base import (
    BaseRule,
    ChecklistEntry,
    RuleOutput,
    RuleResult,
)

# Only addend keys — total_pct is the declared total, not an addend
COMPOSITION_ADDEND_KEYS = {
    "material.composition.cotton_pct",
    "material.composition.polyester_pct",
    "material.composition.elastane_pct",
    "material.composition.viscose_pct",
    "material.composition.other_pct",
}


class CompositionSum100(BaseRule):
    """Check that material.composition.*_pct fields sum to 99-101.

    Evaluates per-document: if multiple docs contain composition fields,
    each document's composition is checked independently.  The rule passes
    if at least one document has a valid sum in 99-101.
    """

    RULE_KEY = "composition_sum_100"

    def evaluate(self, case_id, fields, documents) -> RuleOutput:
        comp_fields = [
            f
            for f in fields
            if f.canonical_key in COMPOSITION_ADDEND_KEYS
            and f.status != "rejected"
        ]

        if not comp_fields:
            return RuleOutput(
                results=[
                    RuleResult(
                        rule_key=self.RULE_KEY,
                        severity="medium",
                        status="warn",
                        message=(
                            "Malzeme kompozisyon alanlari bulunamadi."
                        ),
                    )
                ]
            )

        # Group composition fields by document
        by_doc: dict[str, list] = {}
        for f in comp_fields:
            doc_id = str(f.document_id)
            by_doc.setdefault(doc_id, []).append(f)

        # Evaluate each document's composition
        any_pass = False
        all_field_ids: list[str] = []
        results_detail: list[str] = []

        for doc_id, doc_fields in by_doc.items():
            total = 0.0
            field_ids: list[str] = []
            parse_errors: list[str] = []

            for f in doc_fields:
                try:
                    val = float(
                        f.value.replace("%", "")
                        .replace(",", ".")
                        .strip()
                    )
                    total += val
                    field_ids.append(str(f.id))
                except (ValueError, AttributeError):
                    parse_errors.append(f.canonical_key)

            all_field_ids.extend(field_ids)

            if parse_errors:
                results_detail.append(
                    f"doc {doc_id[:8]}: parse error"
                )
                continue

            if 99.0 <= total <= 101.0:
                any_pass = True
                results_detail.append(
                    f"doc {doc_id[:8]}: {total:.1f}% (gecerli)"
                )
            else:
                results_detail.append(
                    f"doc {doc_id[:8]}: {total:.1f}% (hatali)"
                )

        if any_pass:
            return RuleOutput(
                results=[
                    RuleResult(
                        rule_key=self.RULE_KEY,
                        severity="high",
                        status="pass",
                        message=(
                            "Malzeme kompozisyonu gecerli "
                            f"({'; '.join(results_detail)})."
                        ),
                        related_field_ids=all_field_ids,
                    )
                ]
            )

        # All documents failed
        return RuleOutput(
            results=[
                RuleResult(
                    rule_key=self.RULE_KEY,
                    severity="high",
                    status="fail",
                    message=(
                        "Kompozisyon toplami tutmuyor "
                        f"({'; '.join(results_detail)})"
                    ),
                    related_field_ids=all_field_ids,
                )
            ],
            checklist_entries=[
                ChecklistEntry(
                    type="composition_error",
                    severity="high",
                    title="Kompozisyon Toplami Hatasi",
                    description=(
                        "Malzeme yuzdeleri toplami gecersiz. "
                        "Beklenen aralik: %99-101. "
                        "Lutfen degerleri kontrol edin."
                    ),
                    related_field_id=(
                        all_field_ids[0]
                        if all_field_ids
                        else None
                    ),
                )
            ],
        )
