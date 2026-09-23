from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auditing import record_audit
from app.authorization.service import authorize
from app.authorization.types import Action, RequestContext
from app.database import get_db
from app.dependencies import get_current_user, get_request_context
from app.models import AuditLog, User
from app.schemas import AuditOut

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get("", response_model=list[AuditOut])
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> list[AuditLog]:
    decision = authorize(user, Action.VIEW_AUDIT, context)
    record_audit(
        db,
        user=user,
        username=user.email,
        resource="AUDITORIA",
        resource_id=None,
        action=Action.VIEW_AUDIT,
        decision=decision,
        context=context,
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason)
    statement = (
        select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)
    )
    return list(db.scalars(statement))
