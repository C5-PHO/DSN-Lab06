from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auditing import record_audit
from app.authorization.service import authorize
from app.authorization.types import Action, RequestContext
from app.database import get_db
from app.dependencies import get_current_user, get_request_context
from app.models import Role, User
from app.schemas import UserCreate, UserOut, UserUpdate
from app.security import hash_password

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def _enforce(
    db: Session, actor: User, action: Action, context: RequestContext, resource_id: int | None
) -> None:
    decision = authorize(actor, action, context)
    record_audit(
        db,
        user=actor,
        username=actor.email,
        resource="USUARIO",
        resource_id=resource_id,
        action=action,
        decision=decision,
        context=context,
    )
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason)


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> list[User]:
    _enforce(db, actor, Action.MANAGE_USERS, context, None)
    return list(db.scalars(select(User).order_by(User.id)))


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> User:
    _enforce(db, actor, Action.MANAGE_USERS, context, None)
    email = payload.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    role = db.scalar(select(Role).where(Role.name == payload.role.value))
    if role is None:
        raise HTTPException(status_code=422, detail="Rol inválido")
    user = User(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),
        role=role,
        department=payload.department.upper(),
        security_level=payload.security_level,
        country=payload.country.upper(),
        contract_type=payload.contract_type,
        status=payload.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    action = Action.ASSIGN_ROLES if payload.role is not None else Action.MANAGE_USERS
    _enforce(db, actor, action, context, user_id)
    changes = payload.model_dump(exclude_unset=True)
    role_name = changes.pop("role", None)
    if role_name is not None:
        role = db.scalar(select(Role).where(Role.name == role_name.value))
        if role is None:
            raise HTTPException(status_code=422, detail="Rol inválido")
        target.role = role
    for field, value in changes.items():
        if field in {"department", "country"}:
            value = value.upper()
        setattr(target, field, value)
    db.commit()
    db.refresh(target)
    return target
