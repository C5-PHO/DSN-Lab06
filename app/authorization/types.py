from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RoleName(StrEnum):
    ADMINISTRADOR = "ADMINISTRADOR"
    GERENTE = "GERENTE"
    SUPERVISOR = "SUPERVISOR"
    EMPLEADO = "EMPLEADO"
    AUDITOR = "AUDITOR"
    INVITADO = "INVITADO"


class Action(StrEnum):
    CREATE_DOCUMENT = "CREATE_DOCUMENT"
    READ_DOCUMENT = "READ_DOCUMENT"
    UPDATE_DOCUMENT = "UPDATE_DOCUMENT"
    DELETE_DOCUMENT = "DELETE_DOCUMENT"
    APPROVE_DOCUMENT = "APPROVE_DOCUMENT"
    VIEW_AUDIT = "VIEW_AUDIT"
    MANAGE_USERS = "MANAGE_USERS"
    ASSIGN_ROLES = "ASSIGN_ROLES"


class DecisionResult(StrEnum):
    PERMITIDO = "PERMITIDO"
    DENEGADO = "DENEGADO"


@dataclass(frozen=True)
class RequestContext:
    occurred_at: datetime
    ip_address: str
    location: str
    device: str


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    result: DecisionResult
    reason: str
    failed_policy: str | None = None
