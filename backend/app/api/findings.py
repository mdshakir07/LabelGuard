from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user
from ..db import get_db
from ..models import Finding, User
from ..schemas.inspection import FindingOut
from ..services.audit import log_audit

router = APIRouter(prefix="/findings", tags=["findings"])

VALID_REVIEWS = {"CONFIRMED", "REJECTED", "MANUAL VERIFICATION"}


@router.patch("/{finding_id}", response_model=FindingOut)
def review_finding(
    finding_id: int,
    body: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review_status = body.get("review_status")
    comment = body.get("review_comment", "")
    if review_status not in VALID_REVIEWS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"review_status must be one of {sorted(VALID_REVIEWS)}")

    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    if user.role not in ("reviewer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only reviewer/admin may review findings")

    before = {
        "review_status": finding.review_status,
        "automated_result": finding.automated_result,
    }
    finding.review_status = review_status
    finding.reviewer_id = user.id
    finding.review_comment = comment or None
    finding.reviewed_at = datetime.now(timezone.utc)

    log_audit(db, "review_finding", "finding", entity_id=str(finding.id), actor=user,
              before=before, after={"review_status": review_status, "comment": comment})
    db.commit()
    db.refresh(finding)
    return finding