import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.database import get_db
from app.models.invite import Invite
from app.models.user import User
from app.schemas.invite import CreateInviteRequest, InviteResponse

router = APIRouter(prefix="/invites", tags=["invites"])


@router.post("", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
def create_invite(
    body: CreateInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("buyer", "admin")),
):
    # Check no pending invite already exists for this email from this buyer
    existing = (
        db.query(Invite)
        .filter(
            Invite.buyer_tenant_id == current_user.tenant_id,
            Invite.supplier_email == body.supplier_email,
            Invite.status == "pending",
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pending invite already exists for this email",
        )

    invite = Invite(
        buyer_tenant_id=current_user.tenant_id,
        supplier_email=body.supplier_email,
        token=secrets.token_urlsafe(32),
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.get("", response_model=list[InviteResponse])
def list_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("buyer", "admin")),
):
    invites = (
        db.query(Invite).filter(Invite.buyer_tenant_id == current_user.tenant_id).all()
    )
    return invites
