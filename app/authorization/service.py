from __future__ import annotations

from app.authorization.abac import POLICIES
from app.authorization.rbac import evaluate_rbac
from app.authorization.types import (
    Action,
    AuthorizationDecision,
    DecisionResult,
    RequestContext,
)
from app.models import Document, User


def authorize(
    user: User,
    action: Action,
    context: RequestContext,
    document: Document | None = None,
) -> AuthorizationDecision:
    rbac_decision = evaluate_rbac(user, action)
    if not rbac_decision.allowed:
        return rbac_decision

    for policy_name, policy in POLICIES:
        denial_reason = policy(user, action, document, context)
        if denial_reason:
            return AuthorizationDecision(
                allowed=False,
                result=DecisionResult.DENEGADO,
                reason=denial_reason,
                failed_policy=f"ABAC:{policy_name}",
            )

    return AuthorizationDecision(
        allowed=True,
        result=DecisionResult.PERMITIDO,
        reason="Acceso autorizado por RBAC y todas las políticas ABAC aplicables",
    )
