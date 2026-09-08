from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth.deps import require_or_higher
from ..db import get_db
from ..models import (Assessment, Finding, Inspection, InspectionImage,
                      User)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(user: User = Depends(require_or_higher("inspector")), db: Session = Depends(get_db)):
    total = db.query(func.count(Inspection.id)).scalar()
    by_status = dict(
        db.query(Inspection.status, func.count(Inspection.id)).group_by(Inspection.status).all()
    )
    by_channel = dict(
        db.query(Inspection.channel, func.count(Inspection.id)).group_by(Inspection.channel).all()
    )
    top_categories = (
        db.query(Inspection.category, func.count(Inspection.id))
        .filter(Inspection.category.isnot(None))
        .group_by(Inspection.category)
        .order_by(func.count(Inspection.id).desc())
        .limit(5)
        .all()
    )
    image_count = db.query(func.count(InspectionImage.id)).scalar()
    assessment_counts = dict(
        db.query(Assessment.result, func.count(Assessment.id)).group_by(Assessment.result).all()
    )
    finding_total = db.query(func.count(Finding.id)).scalar()
    reviewed = db.query(func.count(Finding.id)).filter(Finding.reviewed_at.isnot(None)).scalar()
    flagged = db.query(func.count(Finding.id)).filter(
        Finding.automated_result == "POTENTIAL NON-COMPLIANCE").scalar()

    # 30-day inspection trend
    month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = db.query(func.count(Inspection.id)).filter(Inspection.created_at >= month).scalar()

    open_findings = (
        db.query(Finding.review_status, func.count(Finding.id))
        .group_by(Finding.review_status)
        .all()
    )
    return {
        "total_inspections": total,
        "status_breakdown": by_status,
        "channel_breakdown": by_channel,
        "top_categories": [dict(category=c, count=n) for c, n in top_categories],
        "total_images": image_count,
        "assessment_breakdown": assessment_counts,
        "findings": {
            "total": finding_total,
            "reviewed": reviewed,
            "pending_review": finding_total - reviewed,
            "flagged_potential": flagged,
            "review_breakdown": dict(open_findings),
        },
        "created_this_month": this_month,
    }