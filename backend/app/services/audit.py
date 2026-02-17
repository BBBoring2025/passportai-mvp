import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit(
    db: Session,
    actor_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Write an entry to the audit log.

    Does NOT commit — caller must commit the transaction.
    """
    entry = AuditLog(
        actor_user_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(entry)
    return entry
