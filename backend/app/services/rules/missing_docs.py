"""Rule: Case must contain all 5 critical document types."""

from __future__ import annotations

from app.services.rules.base import (
    BaseRule,
    ChecklistEntry,
    RuleOutput,
    RuleResult,
)

REQUIRED_DOC_TYPES = [
    "invoice",
    "packing_list",
    "certificate",
    "test_report",
    "sds",
]

DOC_TYPE_LABELS: dict[str, str] = {
    "invoice": "Ticari Fatura",
    "packing_list": "Ambalaj Listesi",
    "certificate": "Sertifika (OEKO-TEX)",
    "test_report": "Test Raporu",
    "sds": "Guvenlik Bilgi Formu (SDS)",
}


class MissingCriticalDocs(BaseRule):
    """Check that all 5 critical document types are present."""

    RULE_KEY = "missing_critical_docs"

    def evaluate(self, case_id, fields, documents) -> RuleOutput:
        present_types = {
            d.doc_type
            for d in documents
            if d.doc_type and d.processing_status != "error"
        }

        missing = [
            dt
            for dt in REQUIRED_DOC_TYPES
            if dt not in present_types
        ]

        if not missing:
            return RuleOutput(
                results=[
                    RuleResult(
                        rule_key=self.RULE_KEY,
                        severity="high",
                        status="pass",
                        message=(
                            "Tum zorunlu belge turleri mevcut "
                            f"({len(REQUIRED_DOC_TYPES)}"
                            f"/{len(REQUIRED_DOC_TYPES)})."
                        ),
                    )
                ]
            )

        missing_labels = [
            DOC_TYPE_LABELS.get(dt, dt) for dt in missing
        ]
        checklist_entries = [
            ChecklistEntry(
                type="missing_document",
                severity="high",
                title=f"{DOC_TYPE_LABELS.get(dt, dt)} eksik",
                description=(
                    f"{DOC_TYPE_LABELS.get(dt, dt)} belgesi "
                    "bu pakette bulunamadi. "
                    "Lutfen ilgili belgeyi yukleyin."
                ),
            )
            for dt in missing
        ]

        return RuleOutput(
            results=[
                RuleResult(
                    rule_key=self.RULE_KEY,
                    severity="high",
                    status="fail",
                    message=(
                        "Eksik belge(ler): "
                        f"{', '.join(missing_labels)}."
                    ),
                )
            ],
            checklist_entries=checklist_entries,
        )
