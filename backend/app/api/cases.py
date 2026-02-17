import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_role
from app.database import get_db
from app.models.buyer_supplier_link import BuyerSupplierLink
from app.models.case import Case
from app.models.document import Document
from app.models.user import User
from app.schemas.case import CaseCreateResponse, CaseResponse, CreateCaseRequest
from app.schemas.document import DocumentResponse
from app.services.audit import write_audit

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseCreateResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    body: CreateCaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("supplier")),
):
    # Resolve buyer_tenant_id from BuyerSupplierLink
    links = (
        db.query(BuyerSupplierLink)
        .filter(BuyerSupplierLink.supplier_tenant_id == current_user.tenant_id)
        .all()
    )
    if not links:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No buyer linked to your account. Contact your buyer.",
        )
    # MVP: auto-assign first buyer if multiple
    buyer_tenant_id = links[0].buyer_tenant_id

    case = Case(
        reference_no=body.reference_no,
        title=body.reference_no,
        product_group=body.product_group,
        date_from=body.date_from,
        date_to=body.date_to,
        notes=body.notes,
        status="draft",
        supplier_tenant_id=current_user.tenant_id,
        buyer_tenant_id=buyer_tenant_id,
        created_by_user_id=current_user.id,
    )
    db.add(case)
    db.flush()

    write_audit(
        db,
        current_user.id,
        "case.created",
        "case",
        case.id,
        {"reference_no": body.reference_no, "buyer_tenant_id": str(buyer_tenant_id)},
    )

    db.commit()
    db.refresh(case)

    return CaseCreateResponse(case_id=case.id, status=case.status)


@router.get("", response_model=list[CaseResponse])
def list_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "supplier":
        cases = (
            db.query(Case)
            .filter(Case.supplier_tenant_id == current_user.tenant_id)
            .order_by(Case.created_at.desc())
            .all()
        )
    elif current_user.role in ("buyer", "admin"):
        cases = (
            db.query(Case)
            .filter(Case.buyer_tenant_id == current_user.tenant_id)
            .order_by(Case.created_at.desc())
            .all()
        )
    else:
        cases = []

    result = []
    for c in cases:
        resp = CaseResponse.model_validate(c)
        resp.document_count = len(c.documents)
        result.append(resp)
    return result


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    # Tenant isolation
    if current_user.role == "supplier" and case.supplier_tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if current_user.role in ("buyer", "admin") and case.buyer_tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    resp = CaseResponse.model_validate(case)
    resp.document_count = len(case.documents)
    return resp


@router.get("/{case_id}/documents", response_model=list[DocumentResponse])
def list_case_documents(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    # Tenant isolation
    if current_user.role == "supplier" and case.supplier_tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if current_user.role in ("buyer", "admin") and case.buyer_tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    docs = (
        db.query(Document)
        .filter(Document.case_id == case_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return docs
