"""Rule: Quantity in invoice must match quantity in packing list."""

from __future__ import annotations

import re

from app.services.rules.base import (
    BaseRule,
    ChecklistEntry,
    RuleOutput,
    RuleResult,
)

QTY_KEY = "shipment.total_quantity"


def _parse_qty(value: str) -> float | None:
    """Parse a quantity string like '12,000' or '12000 pcs'."""
    cleaned = value.replace(",", "").strip()
    cleaned = re.sub(r"[a-zA-Z\s]+$", "", cleaned)
    try:
        return float(cleaned)
    except ValueError:
        return None


class QtyMismatch(BaseRule):
    """Compare shipment.total_quantity across invoice vs packing_list."""

    RULE_KEY = "qty_mismatch"

    def evaluate(self, case_id, fields, documents) -> RuleOutput:
        doc_type_map = {str(d.id): d.doc_type for d in documents}

        qty_by_type: dict[str, list] = {}
        for f in fields:
            if (
                f.canonical_key == QTY_KEY
                and f.status != "rejected"
            ):
                dt = doc_type_map.get(str(f.document_id))
                if dt:
                    qty_by_type.setdefault(dt, []).append(f)

        invoice_fields = qty_by_type.get("invoice", [])
        packing_fields = qty_by_type.get("packing_list", [])

        if not invoice_fields or not packing_fields:
            return RuleOutput(
                results=[
                    RuleResult(
                        rule_key=self.RULE_KEY,
                        severity="medium",
                        status="warn",
                        message=(
                            "Quantity comparison not possible: "
                            "quantity field missing in invoice "
                            "or packing list."
                        ),
                    )
                ]
            )

        inv_field = invoice_fields[0]
        pack_field = packing_fields[0]
        field_ids = [str(inv_field.id), str(pack_field.id)]

        inv_qty = _parse_qty(inv_field.value)
        pack_qty = _parse_qty(pack_field.value)

        if inv_qty is None or pack_qty is None:
            return RuleOutput(
                results=[
                    RuleResult(
                        rule_key=self.RULE_KEY,
                        severity="high",
                        status="fail",
                        message=(
                            "Quantity values are not numeric: "
                            f"invoice='{inv_field.value}', "
                            f"packing list='{pack_field.value}'."
                        ),
                        related_field_ids=field_ids,
                    )
                ]
            )

        if inv_qty == pack_qty:
            return RuleOutput(
                results=[
                    RuleResult(
                        rule_key=self.RULE_KEY,
                        severity="high",
                        status="pass",
                        message=(
                            f"Quantity matches: {inv_qty:.0f} "
                            "(invoice = packing list)."
                        ),
                        related_field_ids=field_ids,
                    )
                ]
            )

        return RuleOutput(
            results=[
                RuleResult(
                    rule_key=self.RULE_KEY,
                    severity="high",
                    status="fail",
                    message=(
                        "Invoice and packing list quantities do not match "
                        f"(invoice={inv_qty:.0f}, "
                        f"packing={pack_qty:.0f})"
                    ),
                    related_field_ids=field_ids,
                )
            ],
            checklist_entries=[
                ChecklistEntry(
                    type="conflict_detected",
                    severity="high",
                    title="Quantity Mismatch",
                    description=(
                        f"Invoice quantity ({inv_qty:.0f}) does not match "
                        "packing list quantity "
                        f"({pack_qty:.0f})."
                    ),
                    related_field_id=str(inv_field.id),
                )
            ],
        )
