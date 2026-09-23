from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auditing import record_audit
from app.authorization.types import AuthorizationDecision, DecisionResult, RequestContext
from app.database import get_db
from app.dependencies import get_current_user, get_request_context, get_token_payload
from app.models import RevokedToken, User
from app.schemas import LoginRequest, MessageResponse, TokenResponse
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> TokenResponse:
    normalized_email = credentials.email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    valid = bool(user and verify_password(credentials.password, user.password_hash))
    active = bool(user and user.status == "ACTIVO")
    if not valid or not active:
        reason = "Credenciales inválidas" if not valid else "El usuario no se encuentra activo"
        record_audit(
            db,
            user=user,
            username=normalized_email,
            resource="AUTH",
            resource_id=None,
            action="LOGIN",
            decision=AuthorizationDecision(False, DecisionResult.DENEGADO, reason, "AUTH"),
            context=context,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=reason)

    record_audit(
        db,
        user=user,
        username=user.email,
        resource="AUTH",
        resource_id=None,
        action="LOGIN",
        decision=AuthorizationDecision(True, DecisionResult.PERMITIDO, "Autenticación correcta"),
        context=context,
    )
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/logout", response_model=MessageResponse)
def logout(
    payload: dict[str, object] = Depends(get_token_payload),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> MessageResponse:
    expiration = datetime.fromtimestamp(int(payload["exp"]), tz=UTC)
    db.add(RevokedToken(jti=str(payload["jti"]), expires_at=expiration))
    db.commit()
    record_audit(
        db,
        user=user,
        username=user.email,
        resource="AUTH",
        resource_id=None,
        action="LOGOUT",
        decision=AuthorizationDecision(True, DecisionResult.PERMITIDO, "Sesión cerrada"),
        context=context,
    )
    return MessageResponse(message="Sesión cerrada correctamente")
