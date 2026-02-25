"""Rule: Same canonical_key with different values across documents = conflict."""

from __future__ import annotations

from collections import defaultdict

from app.services.rules.base import (
    BaseRule,
    ChecklistEntry,
    RuleOutput,
    RuleResult,
)


class ConflictDetection(BaseRule):
    """Detect fields with same canonical_key but different values across docs."""

    RULE_KEY = "conflict_detection"

    def evaluate(self, case_id, fields, documents) -> RuleOutput:
        # Group fields by canonical_key
        key_values: dict[str, list] = defaultdict(list)
        for f in fields:
            if f.status != "rejected":
                key_values[f.canonical_key].append(f)

        conflicts_found: list[RuleResult] = []
        checklist_entries: list[ChecklistEntry] = []

        for key, field_list in key_values.items():
            if len(field_list) < 2:
                continue

            # Compare normalized values
            unique_values: set[str] = set()
            for f in field_list:
                normalized = (
                    f.value.strip().lower().replace(",", "")
                )
                unique_values.add(normalized)

            if len(unique_values) > 1:
                field_ids = [str(f.id) for f in field_list]
                vals = [f.value for f in field_list]
                val_str = " vs ".join(vals)

                conflicts_found.append(
                    RuleResult(
                        rule_key=self.RULE_KEY,
                        severity="high",
                        status="fail",
                        message=(
                            f"Different values for {key} "
                            f"({val_str})"
                        ),
                        related_field_ids=field_ids,
                    )
                )

                # Mark conflicting fields
                for f in field_list:
                    f.status = "conflict"

                checklist_entries.append(
                    ChecklistEntry(
                        type="conflict_detected",
                        severity="high",
                        title=f"Conflicting Field: {key}",
                        description=(
                            f"'{key}' field contains different values "
                            "across documents: "
                            f"{val_str}. "
                            "Please select the correct value."
                        ),
                        related_field_id=str(field_list[0].id),
                    )
                )

        if not conflicts_found:
            return RuleOutput(
                results=[
                    RuleResult(
                        rule_key=self.RULE_KEY,
                        severity="medium",
                        status="pass",
                        message=(
                            "No conflicting values found "
                            "across documents."
                        ),
                    )
                ]
            )

        return RuleOutput(
            results=conflicts_found,
            checklist_entries=checklist_entries,
        )
