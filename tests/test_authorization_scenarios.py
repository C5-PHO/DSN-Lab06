from __future__ import annotations

from datetime import datetime

import pytest

from app.authorization.service import authorize
from app.authorization.types import Action, RequestContext, RoleName
from app.models import Document, Permission, Role, User
from app.seed import RBAC_MATRIX


def make_user(
    role_name: RoleName,
    *,
    user_id: int = 10,
    department: str = "FINANZAS",
    level: int = 5,
    country: str = "PERU",
    contract: str = "INTERNO",
    user_status: str = "ACTIVO",
) -> User:
    role = Role(name=role_name.value, description="Prueba")
    role.permissions = [
        Permission(name=action.value, description="Prueba") for action in RBAC_MATRIX[role_name]
    ]
    return User(
        id=user_id,
        name="Usuario de prueba",
        email="test@example.com",
        password_hash="unused",
        role=role,
        department=department,
        security_level=level,
        country=country,
        contract_type=contract,
        status=user_status,
    )


def make_document(
    *,
    owner_id: int = 10,
    department: str = "FINANZAS",
    level: int = 3,
    document_status: str = "PENDIENTE",
    country: str = "PERU",
) -> Document:
    return Document(
        id=501,
        title="Documento de prueba",
        description="",
        owner_id=owner_id,
        department=department,
        confidentiality_level=level,
        status=document_status,
        country=country,
    )


def context(*, hour: int = 11, location: str = "PERU", device: str = "CORPORATIVO"):
    return RequestContext(
        occurred_at=datetime(2026, 9, 23, hour, 30),
        ip_address="192.168.10.20",
        location=location,
        device=device,
    )


@pytest.mark.parametrize(
    ("scenario", "user", "action", "document", "request_context", "expected"),
    [
        (
            "1 empleado consulta documento de su área",
            make_user(RoleName.EMPLEADO, level=3),
            Action.READ_DOCUMENT,
            make_document(level=3),
            context(),
            True,
        ),
        (
            "2 empleado consulta documento de otra área",
            make_user(RoleName.EMPLEADO),
            Action.READ_DOCUMENT,
            make_document(department="RRHH"),
            context(),
            False,
        ),
        (
            "3 supervisor aprueba documento de su área",
            make_user(RoleName.SUPERVISOR),
            Action.APPROVE_DOCUMENT,
            make_document(),
            context(),
            True,
        ),
        (
            "4 empleado intenta aprobar documento",
            make_user(RoleName.EMPLEADO),
            Action.APPROVE_DOCUMENT,
            make_document(),
            context(),
            False,
        ),
        (
            "5 usuario nivel 2 consulta documento nivel 4",
            make_user(RoleName.EMPLEADO, level=2),
            Action.READ_DOCUMENT,
            make_document(level=4),
            context(),
            False,
        ),
        (
            "6 gerente elimina documento",
            make_user(RoleName.GERENTE),
            Action.DELETE_DOCUMENT,
            make_document(),
            context(),
            True,
        ),
        (
            "7 auditor intenta modificar documento",
            make_user(RoleName.AUDITOR),
            Action.UPDATE_DOCUMENT,
            make_document(),
            context(),
            False,
        ),
        (
            "8 usuario inactivo intenta acceder",
            make_user(RoleName.EMPLEADO, user_status="INACTIVO"),
            Action.READ_DOCUMENT,
            make_document(),
            context(),
            False,
        ),
        (
            "9 documento confidencial accedido fuera de horario",
            make_user(RoleName.EMPLEADO),
            Action.READ_DOCUMENT,
            make_document(level=4),
            context(hour=22),
            False,
        ),
        (
            "10 documento nivel 5 desde dispositivo personal",
            make_user(RoleName.EMPLEADO),
            Action.READ_DOCUMENT,
            make_document(level=5),
            context(device="PERSONAL"),
            False,
        ),
        (
            "11 invitado accede a documento público",
            make_user(RoleName.INVITADO, department="PUBLICO", level=1, contract="EXTERNO"),
            Action.READ_DOCUMENT,
            make_document(department="PUBLICO", level=1, document_status="PUBLICADO"),
            context(),
            True,
        ),
        (
            "12 invitado accede a documento confidencial",
            make_user(RoleName.INVITADO, department="PUBLICO", level=5, contract="EXTERNO"),
            Action.READ_DOCUMENT,
            make_document(department="PUBLICO", level=3, document_status="PUBLICADO"),
            context(),
            False,
        ),
        (
            "13 administrador elimina documento de otra área",
            make_user(RoleName.ADMINISTRADOR, department="TI"),
            Action.DELETE_DOCUMENT,
            make_document(department="LEGAL"),
            context(),
            True,
        ),
        (
            "14 supervisor modifica documento ajeno",
            make_user(RoleName.SUPERVISOR, user_id=10),
            Action.UPDATE_DOCUMENT,
            make_document(owner_id=99),
            context(),
            False,
        ),
        (
            "15 gerente modifica documento ajeno de su área",
            make_user(RoleName.GERENTE, user_id=10),
            Action.UPDATE_DOCUMENT,
            make_document(owner_id=99),
            context(),
            True,
        ),
        (
            "16 solicitud desde un país distinto",
            make_user(RoleName.EMPLEADO),
            Action.READ_DOCUMENT,
            make_document(),
            context(location="CHILE"),
            False,
        ),
        (
            "17 auditor consulta el registro",
            make_user(RoleName.AUDITOR),
            Action.VIEW_AUDIT,
            None,
            context(),
            True,
        ),
    ],
)
def test_authorization_scenarios(
    scenario: str,
    user: User,
    action: Action,
    document: Document | None,
    request_context: RequestContext,
    expected: bool,
):
    decision = authorize(user, action, request_context, document)
    assert decision.allowed is expected, f"{scenario}: {decision.reason}"
