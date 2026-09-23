from __future__ import annotations

from sqlalchemy.orm import Session

from app.authorization.types import Action, AuthorizationDecision, RequestContext
from app.models import AuditLog, User


def record_audit(
    db: Session,
    *,
    user: User | None,
    username: str,
    resource: str,
    resource_id: str | int | None,
    action: Action | str,
    decision: AuthorizationDecision,
    context: RequestContext,
) -> AuditLog:
    log = AuditLog(
        user_id=user.id if user else None,
        username=username,
        resource=resource,
        resource_id=str(resource_id) if resource_id is not None else None,
        action=action.value if isinstance(action, Action) else action,
        result=decision.result.value,
        reason=decision.reason,
        ip_address=context.ip_address,
        location=context.location,
        device=context.device,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
