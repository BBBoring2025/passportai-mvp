import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.buyer_supplier_link import BuyerSupplierLink
from app.models.invite import Invite
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import (
    AcceptInviteRequest,
    AcceptInviteResponse,
    LoginRequest,
    LoginResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    token = create_access_token(user.id, user.role, user.tenant_id)
    return LoginResponse(access_token=token, role=user.role, tenant_id=user.tenant_id)


@router.post("/accept-invite", response_model=AcceptInviteResponse)
def accept_invite(body: AcceptInviteRequest, db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.token == body.token).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if invite.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already used")
    now = datetime.now(UTC)
    expires = invite.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite expired")

    # Check if user already exists
    existing = db.query(User).filter(User.email == invite.supplier_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists. Please log in."
        )

    # Create supplier tenant
    slug = "supplier-" + secrets.token_hex(4)
    supplier_tenant = Tenant(
        name=f"{body.full_name}'s Company",
        slug=slug,
        tenant_type="supplier",
    )
    db.add(supplier_tenant)
    db.flush()

    # Create user
    user = User(
        email=invite.supplier_email,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role="supplier",
        tenant_id=supplier_tenant.id,
    )
    db.add(user)
    db.flush()

    # Create buyer-supplier link
    link = BuyerSupplierLink(
        buyer_tenant_id=invite.buyer_tenant_id,
        supplier_tenant_id=supplier_tenant.id,
        invite_id=invite.id,
    )
    db.add(link)

    # Mark invite accepted
    invite.status = "accepted"
    invite.accepted_at = datetime.now(UTC)

    db.commit()

    token = create_access_token(user.id, user.role, supplier_tenant.id)
    return AcceptInviteResponse(
        access_token=token,
        role=user.role,
        tenant_id=supplier_tenant.id,
        message="Account created successfully",
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        tenant_id=current_user.tenant_id,
        tenant_name=current_user.tenant.name,
        tenant_type=current_user.tenant.tenant_type,
    )
