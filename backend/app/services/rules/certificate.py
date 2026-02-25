"""Rule: Certificate expiration date must not be in the past."""

from __future__ import annotations

from datetime import date, datetime

from app.services.rules.base import (
    BaseRule,
    ChecklistEntry,
    RuleOutput,
    RuleResult,
)

VALIDITY_KEY = "certificate.oekotex.valid_until"

DATE_FORMATS = [
    "%Y-%m-%d",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
]


class CertificateValidity(BaseRule):
    """Check certificate.*.valid_until is not expired."""

    RULE_KEY = "certificate_validity"

    def evaluate(self, case_id, fields, documents) -> RuleOutput:
        validity_fields = [
            f
            for f in fields
            if f.canonical_key == VALIDITY_KEY
            and f.status != "rejected"
        ]

        if not validity_fields:
            return RuleOutput(
                results=[
                    RuleResult(
                        rule_key=self.RULE_KEY,
                        severity="medium",
                        status="warn",
                        message=(
                            "Certificate validity date not found."
                        ),
                    )
                ]
            )

        field = validity_fields[0]
        field_ids = [str(field.id)]

        # Parse date
        valid_until = None
        for fmt in DATE_FORMATS:
            try:
                valid_until = datetime.strptime(
                    field.value.strip(), fmt
                ).date()
                break
            except ValueError:
                continue

        if valid_until is None:
            return RuleOutput(
                results=[
                    RuleResult(
                        rule_key=self.RULE_KEY,
                        severity="high",
                        status="fail",
                        message=(
                            "Certificate date unreadable: "
                            f"'{field.value}'."
                        ),
                        related_field_ids=field_ids,
                    )
                ]
            )

        today = date.today()
        if valid_until >= today:
            return RuleOutput(
                results=[
                    RuleResult(
                        rule_key=self.RULE_KEY,
                        severity="high",
                        status="pass",
                        message=(
                            f"Certificate valid: {valid_until} "
                            f"(today: {today})."
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
                        "Certificate expired "
                        f"({VALIDITY_KEY}, {valid_until})"
                    ),
                    related_field_ids=field_ids,
                )
            ],
            checklist_entries=[
                ChecklistEntry(
                    type="expired_document",
                    severity="high",
                    title="Expired Certificate",
                    description=(
                        f"OEKO-TEX certificate expired on {valid_until}. "
                        "Please upload an up-to-date certificate."
                    ),
                    related_field_id=str(field.id),
                )
            ],
        )
