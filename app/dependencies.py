from __future__ import annotations

from datetime import UTC, datetime

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.authorization.types import RequestContext
from app.config import settings
from app.database import get_db
from app.models import RevokedToken, User
from app.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        ) from exc
    jti = str(payload.get("jti", ""))
    if not jti or db.scalar(select(RevokedToken).where(RevokedToken.jti == jti)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")
    return payload


def get_current_user(
    payload: dict[str, object] = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> User:
    try:
        user_id = int(str(payload["sub"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        ) from exc
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado"
        )
    return user


def get_request_context(
    request: Request,
    x_device: str | None = Header(default=None),
    x_location: str | None = Header(default=None),
    x_access_time: str | None = Header(default=None),
) -> RequestContext:
    occurred_at = datetime.now(UTC)
    if settings.allow_context_headers and x_access_time:
        try:
            occurred_at = datetime.fromisoformat(x_access_time.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="X-Access-Time debe ser ISO 8601") from exc
    device = (x_device or "PERSONAL").strip().upper()
    location = (x_location or "PERU").strip().upper()
    ip_address = request.client.host if request.client else "unknown"
    return RequestContext(
        occurred_at=occurred_at,
        ip_address=ip_address,
        location=location,
        device=device,
    )
