from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.authorization.types import Action, RoleName
from app.models import ABACPolicy, Document, Permission, Role, User
from app.security import hash_password

ROLE_DESCRIPTIONS = {
    RoleName.ADMINISTRADOR: "Administra usuarios, roles y configuraciones",
    RoleName.GERENTE: "Supervisa documentos de su área",
    RoleName.SUPERVISOR: "Revisa y aprueba documentos",
    RoleName.EMPLEADO: "Crea y consulta documentos de su área",
    RoleName.AUDITOR: "Consulta documentos y registros de auditoría",
    RoleName.INVITADO: "Acceso temporal a determinados documentos",
}

RBAC_MATRIX = {
    RoleName.ADMINISTRADOR: set(Action),
    RoleName.GERENTE: {
        Action.CREATE_DOCUMENT,
        Action.READ_DOCUMENT,
        Action.UPDATE_DOCUMENT,
        Action.DELETE_DOCUMENT,
        Action.APPROVE_DOCUMENT,
        Action.VIEW_AUDIT,
    },
    RoleName.SUPERVISOR: {
        Action.CREATE_DOCUMENT,
        Action.READ_DOCUMENT,
        Action.UPDATE_DOCUMENT,
        Action.APPROVE_DOCUMENT,
    },
    RoleName.EMPLEADO: {
        Action.CREATE_DOCUMENT,
        Action.READ_DOCUMENT,
        Action.UPDATE_DOCUMENT,
    },
    RoleName.AUDITOR: {Action.READ_DOCUMENT, Action.VIEW_AUDIT},
    RoleName.INVITADO: {Action.READ_DOCUMENT},
}

POLICY_DESCRIPTIONS = {
    "DEPARTAMENTO": "Restringe los recursos al departamento aplicable del usuario.",
    "NIVEL_SEGURIDAD": "Exige nivel de seguridad suficiente para la confidencialidad.",
    "PROPIEDAD": "Restringe modificaciones al propietario, salvo gerente o administrador.",
    "HORARIO": "Restringe consultas de nivel 4 o 5 al horario de 08:00 a 18:00.",
    "PAIS": "Exige coincidencia entre país del usuario, solicitud y documento.",
    "DISPOSITIVO": "Exige dispositivo corporativo para consultar niveles 4 o 5.",
    "ESTADO_USUARIO": "Solo permite acceso a usuarios activos.",
    "INVITADOS": "Limita invitados externos a documentos publicados de nivel 1.",
}

DEMO_USERS = (
    (
        "Admin SecureDocs",
        "admin@securedocs.local",
        RoleName.ADMINISTRADOR,
        "TI",
        5,
        "PERU",
        "INTERNO",
    ),
    (
        "Gabriela Gerente",
        "gerente@securedocs.local",
        RoleName.GERENTE,
        "FINANZAS",
        5,
        "PERU",
        "INTERNO",
    ),
    (
        "Carlos Supervisor",
        "supervisor@securedocs.local",
        RoleName.SUPERVISOR,
        "FINANZAS",
        4,
        "PERU",
        "INTERNO",
    ),
    (
        "Ana Empleada",
        "empleado@securedocs.local",
        RoleName.EMPLEADO,
        "FINANZAS",
        3,
        "PERU",
        "INTERNO",
    ),
    (
        "Alonso Auditor",
        "auditor@securedocs.local",
        RoleName.AUDITOR,
        "AUDITORIA",
        5,
        "PERU",
        "INTERNO",
    ),
    (
        "Invitado Externo",
        "invitado@securedocs.local",
        RoleName.INVITADO,
        "PUBLICO",
        1,
        "PERU",
        "EXTERNO",
    ),
)


def seed_database(db: Session) -> None:
    permission_by_action: dict[Action, Permission] = {}
    for action in Action:
        permission = db.scalar(select(Permission).where(Permission.name == action.value))
        if not permission:
            permission = Permission(
                name=action.value, description=action.value.replace("_", " ").title()
            )
            db.add(permission)
            db.flush()
        permission_by_action[action] = permission

    role_by_name: dict[RoleName, Role] = {}
    for role_name, actions in RBAC_MATRIX.items():
        role = db.scalar(select(Role).where(Role.name == role_name.value))
        if not role:
            role = Role(name=role_name.value, description=ROLE_DESCRIPTIONS[role_name])
            db.add(role)
            db.flush()
        role.permissions = [permission_by_action[action] for action in actions]
        role_by_name[role_name] = role

    for code, description in POLICY_DESCRIPTIONS.items():
        if not db.scalar(select(ABACPolicy).where(ABACPolicy.code == code)):
            db.add(
                ABACPolicy(code=code, name=code.replace("_", " ").title(), description=description)
            )

    for name, email, role_name, department, level, country, contract_type in DEMO_USERS:
        if not db.scalar(select(User).where(User.email == email)):
            db.add(
                User(
                    name=name,
                    email=email,
                    password_hash=hash_password("Secure123!"),
                    role=role_by_name[role_name],
                    department=department,
                    security_level=level,
                    country=country,
                    contract_type=contract_type,
                    status="ACTIVO",
                )
            )
    db.commit()

    owner = db.scalar(select(User).where(User.email == "empleado@securedocs.local"))
    if owner and not db.scalar(select(Document).limit(1)):
        db.add_all(
            [
                Document(
                    title="Presupuesto anual 2027",
                    description="Presupuesto pendiente de aprobación.",
                    owner_id=owner.id,
                    department="FINANZAS",
                    confidentiality_level=3,
                    status="PENDIENTE",
                    country="PERU",
                ),
                Document(
                    title="Política pública de proveedores",
                    description="Documento público disponible para invitados.",
                    owner_id=owner.id,
                    department="PUBLICO",
                    confidentiality_level=1,
                    status="PUBLICADO",
                    country="PERU",
                ),
            ]
        )
        db.commit()
