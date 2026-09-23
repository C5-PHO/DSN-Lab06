from __future__ import annotations

from collections.abc import Callable

from app.authorization.types import Action, RequestContext, RoleName
from app.models import Document, User

Policy = Callable[[User, Action, Document | None, RequestContext], str | None]


def active_user(user: User, _: Action, __: Document | None, ___: RequestContext) -> str | None:
    if user.status != "ACTIVO":
        return "El usuario no se encuentra activo"
    return None


def same_department(
    user: User, action: Action, document: Document | None, _: RequestContext
) -> str | None:
    scoped_roles = {RoleName.EMPLEADO, RoleName.SUPERVISOR, RoleName.GERENTE}
    document_actions = {
        Action.CREATE_DOCUMENT,
        Action.READ_DOCUMENT,
        Action.UPDATE_DOCUMENT,
        Action.DELETE_DOCUMENT,
        Action.APPROVE_DOCUMENT,
    }
    if document and user.role.name in scoped_roles and action in document_actions:
        if user.department != document.department:
            return "El documento pertenece a otro departamento"
    return None


def sufficient_security_level(
    user: User, action: Action, document: Document | None, _: RequestContext
) -> str | None:
    if document and action in {
        Action.CREATE_DOCUMENT,
        Action.READ_DOCUMENT,
        Action.UPDATE_DOCUMENT,
        Action.DELETE_DOCUMENT,
        Action.APPROVE_DOCUMENT,
    }:
        if user.security_level < document.confidentiality_level:
            return "Nivel de seguridad insuficiente"
    return None


def document_ownership(
    user: User, action: Action, document: Document | None, _: RequestContext
) -> str | None:
    if (
        document
        and action == Action.UPDATE_DOCUMENT
        and user.role.name not in {RoleName.ADMINISTRADOR, RoleName.GERENTE}
        and user.id != document.owner_id
    ):
        return "Solo el propietario, un gerente o un administrador puede modificar el documento"
    return None


def authorized_schedule(
    _: User, action: Action, document: Document | None, context: RequestContext
) -> str | None:
    if document and action == Action.READ_DOCUMENT and document.confidentiality_level >= 4:
        if not 8 <= context.occurred_at.hour < 18:
            return "Documento altamente confidencial fuera del horario de 08:00 a 18:00"
    return None


def matching_country(
    user: User, action: Action, document: Document | None, context: RequestContext
) -> str | None:
    if document and action == Action.READ_DOCUMENT:
        if user.country != document.country or context.location != document.country:
            return "El país del usuario o de la solicitud no coincide con el documento"
    return None


def corporate_device(
    _: User, action: Action, document: Document | None, context: RequestContext
) -> str | None:
    if (
        document
        and action == Action.READ_DOCUMENT
        and document.confidentiality_level >= 4
        and context.device != "CORPORATIVO"
    ):
        return "Los documentos de nivel 4 o 5 requieren un dispositivo corporativo"
    return None


def guest_access(
    user: User, action: Action, document: Document | None, _: RequestContext
) -> str | None:
    if user.role.name != RoleName.INVITADO:
        return None
    if action != Action.READ_DOCUMENT or document is None:
        return "Los invitados solo pueden consultar documentos"
    if user.contract_type != "EXTERNO":
        return "El invitado debe tener contrato externo"
    if document.confidentiality_level > 1 or document.status != "PUBLICADO":
        return "El invitado solo puede consultar documentos públicos de nivel 1"
    return None


POLICIES: tuple[tuple[str, Policy], ...] = (
    ("ESTADO_USUARIO", active_user),
    ("DEPARTAMENTO", same_department),
    ("NIVEL_SEGURIDAD", sufficient_security_level),
    ("PROPIEDAD", document_ownership),
    ("HORARIO", authorized_schedule),
    ("PAIS", matching_country),
    ("DISPOSITIVO", corporate_device),
    ("INVITADOS", guest_access),
)
