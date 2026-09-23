from __future__ import annotations

from app.authorization.types import Action, AuthorizationDecision, DecisionResult
from app.models import User


def evaluate_rbac(user: User, action: Action) -> AuthorizationDecision:
    granted = {permission.name for permission in user.role.permissions}
    if action.value not in granted:
        return AuthorizationDecision(
            allowed=False,
            result=DecisionResult.DENEGADO,
            reason=f"El rol {user.role.name} no posee el permiso {action.value}",
            failed_policy="RBAC",
        )
    return AuthorizationDecision(
        allowed=True,
        result=DecisionResult.PERMITIDO,
        reason=f"Permiso {action.value} concedido al rol {user.role.name}",
    )
