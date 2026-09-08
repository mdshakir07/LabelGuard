from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..models import AuditLog, User


def log_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    actor: Optional[User] = None,
    system: bool = False,
    before: Optional[dict] = None,
    after: Optional[dict] = None,
) -> AuditLog:
    entry = AuditLog(
        actor_type="system" if system else "user",
        actor_id=None if system else (actor.id if actor else None),
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        before=before,
        after=after,
    )
    db.add(entry)
    db.flush()
    return entry


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()