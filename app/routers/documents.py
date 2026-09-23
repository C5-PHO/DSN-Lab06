from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auditing import record_audit
from app.authorization.service import authorize
from app.authorization.types import Action, RequestContext
from app.database import get_db
from app.dependencies import get_current_user, get_request_context
from app.models import Document, User
from app.schemas import DocumentCreate, DocumentOut, DocumentUpdate, MessageResponse

router = APIRouter(prefix="/documentos", tags=["Documentos"])


def _audit_decision(
    db: Session,
    user: User,
    action: Action,
    document: Document | None,
    context: RequestContext,
):
    decision = authorize(user, action, context, document)
    record_audit(
        db,
        user=user,
        username=user.email,
        resource="DOCUMENTO",
        resource_id=document.id if document and document.id else None,
        action=action,
        decision=decision,
        context=context,
    )
    return decision


def _enforce(
    db: Session,
    user: User,
    action: Action,
    document: Document | None,
    context: RequestContext,
) -> None:
    decision = _audit_decision(db, user, action, document, context)
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason)


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> list[Document]:
    accessible: list[Document] = []
    for document in db.scalars(select(Document).order_by(Document.id)):
        if _audit_decision(db, user, Action.READ_DOCUMENT, document, context).allowed:
            accessible.append(document)
    return accessible


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    _enforce(db, user, Action.READ_DOCUMENT, document, context)
    return document


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> Document:
    document = Document(
        title=payload.title,
        description=payload.description,
        owner_id=user.id,
        department=payload.department.upper(),
        confidentiality_level=payload.confidentiality_level,
        status=payload.status,
        country=payload.country.upper(),
    )
    _enforce(db, user, Action.CREATE_DOCUMENT, document, context)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.put("/{document_id}", response_model=DocumentOut)
def update_document(
    document_id: int,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    projected = Document(
        id=document.id,
        title=document.title,
        description=document.description,
        owner_id=document.owner_id,
        department=document.department,
        confidentiality_level=document.confidentiality_level,
        status=document.status,
        country=document.country,
    )
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if field in {"department", "country"}:
            value = value.upper()
        setattr(projected, field, value)
    _enforce(db, user, Action.UPDATE_DOCUMENT, projected, context)
    for field in changes:
        setattr(document, field, getattr(projected, field))
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", response_model=MessageResponse)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> MessageResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    _enforce(db, user, Action.DELETE_DOCUMENT, document, context)
    db.delete(document)
    db.commit()
    return MessageResponse(message="Documento eliminado")


@router.post("/{document_id}/aprobar", response_model=DocumentOut)
def approve_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    _enforce(db, user, Action.APPROVE_DOCUMENT, document, context)
    document.status = "PUBLICADO"
    db.commit()
    db.refresh(document)
    return document
