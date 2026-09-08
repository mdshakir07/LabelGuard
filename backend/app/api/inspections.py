from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from ..auth.deps import get_current_user, require_or_higher, require_roles, require_writer
from ..db import get_db
from ..models import Assessment, ExtractedField, Finding, Inspection, User  # noqa: F401
from ..schemas.inspection import (CategoryPatch, FieldPatch, InspectionCreate,
                                  InspectionListItem, InspectionOut)
from ..services.audit import log_audit
from ..services.category import suggest_categories

router = APIRouter(prefix="/inspections", tags=["inspections"])


def _public_id(db: Session) -> str:
    year = str(date.today().year)
    prefix = f"IN-{year}-"
    count = db.query(func.count(Inspection.id)).filter(Inspection.public_id.like(f"{prefix}%")).scalar()
    return f"{prefix}{(count + 1):04d}"


@router.post("", response_model=InspectionListItem, status_code=status.HTTP_201_CREATED)
def create_inspection(
    body: InspectionCreate,
    user: User = Depends(require_writer),
    db: Session = Depends(get_db),
):
    insp = Inspection(
        public_id=_public_id(db),
        inspector_id=user.id,
        location=body.location,
        channel=body.channel,
        category=body.category,
        inspection_date=body.inspection_date,
        package_structure=body.package_structure,
        origin=body.origin,
        special_status=body.special_status,
        product_name_hint=body.product_name_hint,
        status="draft",
    )
    db.add(insp)
    db.flush()
    log_audit(db, "create", "inspection", entity_id=insp.public_id, actor=user,
              after={"status": "draft", "channel": body.channel})
    db.commit()
    db.refresh(insp)
    return _to_list_item(insp)


@router.get("", response_model=dict)
def list_inspections(
    status_filter: Optional[str] = Query(None, alias="status"),
    channel: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_or_higher("inspector")),
    db: Session = Depends(get_db),
):
    query = db.query(Inspection)
    if status_filter:
        query = query.filter(Inspection.status == status_filter)
    if channel:
        query = query.filter(Inspection.channel == channel)
    if category:
        query = query.filter(Inspection.category == category)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Inspection.public_id.ilike(like)) | (Inspection.location.ilike(like))
            | (Inspection.category.ilike(like))
        )
    total = query.count()
    rows = query.order_by(Inspection.created_at.desc()).offset(offset).limit(limit).all()
    fa_count = {
        row: c for row, c in db.query(Finding.inspection_id, func.count(Finding.id))
        .group_by(Finding.inspection_id).all()
    }
    items = [
        _to_list_item(r, image_count=len(r.images), finding_count=fa_count.get(r.id, 0))
        for r in rows
    ]
    return {"items": items, "total": total}


@router.get("/{inspection_id}", response_model=InspectionOut)
def get_inspection(
    inspection_id: int,
    user: User = Depends(require_or_higher("inspector")),
    db: Session = Depends(get_db),
):
    insp = db.query(Inspection).options(
        joinedload(Inspection.images),
    ).filter(Inspection.id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    insp.fields  # eager-load via relationship access (default lazy in this session)
    insp.assessments
    for a in insp.assessments:
        a.findings
    return insp


@router.get("/{inspection_id}/fields")
def get_fields(
    inspection_id: int,
    user: User = Depends(require_or_higher("inspector")),
    db: Session = Depends(get_db),
):
    insp = db.get(Inspection, inspection_id)
    if not insp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    return [f for f in insp.fields]


@router.patch("/{inspection_id}/fields/{field_id}")
def edit_field(
    inspection_id: int,
    field_id: int,
    body: FieldPatch,
    user: User = Depends(require_writer),
    db: Session = Depends(get_db),
):
    """Inspector corrects an extracted field (PRD §24 / §31 S08).

    Raw and normalized values are updated together; `is_edited`, editor and
    timestamp are recorded for audit. Correction is safe only while the
    inspection is not yet closed (original immutable evidence untouched).
    """
    insp = db.get(Inspection, inspection_id)
    if not insp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    if insp.status == "closed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inspection closed; fields locked")

    field = db.query(ExtractedField).filter(
        ExtractedField.id == field_id, ExtractedField.inspection_id == inspection_id
    ).first()
    if not field:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")

    before = {"raw": field.raw, "normalized": field.normalized, "is_edited": field.is_edited}
    field.raw = body.raw
    field.normalized = body.normalized
    field.confidence = body.confidence
    field.is_edited = True
    field.edited_by = user.id
    field.edited_at = datetime.now(timezone.utc)

    log_audit(db, "field_edit", "extracted_field", entity_id=str(field.id),
              actor=user, before=before, after={"raw": body.raw, "normalized": body.normalized})
    db.commit()
    db.refresh(field)
    return field


@router.post("/{inspection_id}/review", response_model=InspectionOut)
def review_inspection(
    inspection_id: int,
    user: User = Depends(require_roles("reviewer", "admin")),
    db: Session = Depends(get_db),
):
    """Human review completes: reviewer marks the inspection reviewed (PRD §21).

    Pre-condition: every automated finding has a human decision (CONFIRMED /
    REJECTED / MANUAL VERIFICATION). No pending findings may remain — an
    automated result alone is never a legal conclusion.
    """
    insp = db.get(Inspection, inspection_id)
    if not insp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    if insp.status != "ready_for_review":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Only inspections that are ready_for_review can be marked reviewed")

    pending = db.query(Finding).filter(
        Finding.inspection_id == inspection_id, Finding.review_status == "pending"
    ).count()
    if pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"{pending} finding(s) still pending human review")

    before = {"status": insp.status}
    insp.status = "reviewed"
    log_audit(db, "review_inspection", "inspection", entity_id=insp.public_id, actor=user,
              before=before, after={"status": "reviewed"})
    db.commit()
    db.refresh(insp)
    return insp


@router.post("/{inspection_id}/close", response_model=InspectionOut)
def close_inspection(
    inspection_id: int,
    user: User = Depends(require_roles("reviewer", "admin")),
    db: Session = Depends(get_db),
):
    """Final state: inspection CLOSED with audit trail (PRD §21)."""
    insp = db.get(Inspection, inspection_id)
    if not insp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    if insp.status == "closed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inspection already closed")
    if insp.status not in ("ready_for_review", "reviewed"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Cannot close inspection in state {insp.status}")

    pending = db.query(Finding).filter(
        Finding.inspection_id == inspection_id, Finding.review_status == "pending"
    ).count()
    if pending:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"{pending} finding(s) still pending human review")

    before = {"status": insp.status, "closed_at": insp.closed_at}
    insp.status = "closed"
    insp.closed_at = datetime.now(timezone.utc)
    log_audit(db, "close_inspection", "inspection", entity_id=insp.public_id, actor=user,
              before=before, after={"status": "closed", "closed_at": str(insp.closed_at)})
    db.commit()
    db.refresh(insp)
    return insp


@router.get("/{inspection_id}/category-suggestion")
def category_suggestion(
    inspection_id: int,
    user: User = Depends(require_or_higher("inspector")),
    db: Session = Depends(get_db),
):
    """Suggest commodity categories from metadata + extracted product (PRD §18).
    Suggestion only — the inspector confirms/overrides."""
    insp = db.get(Inspection, inspection_id)
    if not insp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")

    extracted_product = None
    row = db.query(ExtractedField).filter(
        ExtractedField.inspection_id == inspection_id,
        ExtractedField.field == "product_name",
    ).first()
    if row:
        extracted_product = row.raw

    suggestions = suggest_categories(
        product_name_hint=insp.product_name_hint,
        special_status=insp.special_status,
        extracted_product=extracted_product,
        category=insp.category,
    )
    return {"current": insp.category, "suggestions": suggestions}


@router.patch("/{inspection_id}/category", response_model=InspectionOut)
def set_category(
    inspection_id: int,
    body: CategoryPatch,
    user: User = Depends(require_writer),
    db: Session = Depends(get_db),
):
    """Inspector confirms/corrects the commodity category before applicability.

    Changing the category invalidates assessments computed under the previous
    applicability context: existing Assessment/Finding rows are cleared and the
    client re-runs POST /inspections/{id}/assess so results reflect the
    confirmed category. Original evidence (images/OCR/fields) is untouched.
    """
    insp = db.get(Inspection, inspection_id)
    if not insp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    if insp.status == "closed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inspection closed; category locked")

    before = {"category": insp.category}
    insp.category = body.category
    db.query(Finding).filter(Finding.inspection_id == inspection_id).delete()
    db.query(Assessment).filter(Assessment.inspection_id == inspection_id).delete()
    log_audit(db, "category_confirmed", "inspection", entity_id=insp.public_id, actor=user,
              before=before, after={"category": body.category})
    db.commit()
    db.refresh(insp)
    return insp


def _to_list_item(insp: Inspection, image_count: int = 0, finding_count: int = 0) -> InspectionListItem:
    return InspectionListItem(
        id=insp.id, public_id=insp.public_id, location=insp.location, channel=insp.channel,
        inspection_date=insp.inspection_date, category=insp.category, status=insp.status,
        ruleset_version=insp.ruleset_version, created_at=insp.created_at,
        image_count=image_count or len(insp.images), finding_count=finding_count,
    )