from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.authorization.types import RoleName


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str


class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=180)
    department: str = Field(min_length=2, max_length=80)
    security_level: int = Field(ge=1, le=5)
    country: str = Field(min_length=2, max_length=80)
    contract_type: str = Field(default="INTERNO", pattern="^(INTERNO|EXTERNO)$")
    status: str = Field(default="ACTIVO", pattern="^(ACTIVO|INACTIVO|SUSPENDIDO)$")


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: RoleName = RoleName.EMPLEADO


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    department: str | None = Field(default=None, min_length=2, max_length=80)
    security_level: int | None = Field(default=None, ge=1, le=5)
    country: str | None = Field(default=None, min_length=2, max_length=80)
    contract_type: str | None = Field(default=None, pattern="^(INTERNO|EXTERNO)$")
    status: str | None = Field(default=None, pattern="^(ACTIVO|INACTIVO|SUSPENDIDO)$")
    role: RoleName | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: RoleOut
    created_at: datetime


class DocumentCreate(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    description: str = Field(default="", max_length=4000)
    department: str = Field(min_length=2, max_length=80)
    confidentiality_level: int = Field(ge=1, le=5)
    status: str = Field(default="BORRADOR", pattern="^(BORRADOR|PENDIENTE|PUBLICADO)$")
    country: str = Field(min_length=2, max_length=80)


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=4000)
    department: str | None = Field(default=None, min_length=2, max_length=80)
    confidentiality_level: int | None = Field(default=None, ge=1, le=5)
    status: str | None = Field(default=None, pattern="^(BORRADOR|PENDIENTE|PUBLICADO)$")
    country: str | None = Field(default=None, min_length=2, max_length=80)


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    owner_id: int
    department: str
    confidentiality_level: int
    status: str
    country: str
    created_at: datetime
    updated_at: datetime


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    username: str
    resource: str
    resource_id: str | None
    action: str
    result: str
    reason: str
    ip_address: str
    location: str
    device: str
    created_at: datetime


class MessageResponse(BaseModel):
    message: str
