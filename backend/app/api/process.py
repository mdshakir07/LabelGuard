import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth.deps import require_writer
from ..db import SessionLocal, get_db
from ..models import Inspection, User
from ..services.audit import log_audit
from ..services.process import process_inspection

router = APIRouter(prefix="/inspections", tags=["process"])
logger = logging.getLogger("app.api.process")


@router.post("/{inspection_id}/process")
def start_processing(
    inspection_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_writer),
    db: Session = Depends(get_db),
):
    insp = db.get(Inspection, inspection_id)
    if not insp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    if insp.status in ("processing", "ready_for_review", "reviewed", "closed"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Inspection already in status {insp.status}")
    if not insp.images:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Upload at least one image before processing")

    log_audit(db, "process_start", "inspection", entity_id=insp.public_id, actor=user)
    db.commit()

    def _run() -> None:
        with SessionLocal() as session:
            process_inspection(session, session.get(Inspection, inspection_id))

    background_tasks.add_task(_run)
    return {"status": "processing", "inspection_id": inspection_id, "public_id": insp.public_id}


@router.post("/{inspection_id}/assess")
def re_assess(
    inspection_id: int,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_writer),
    db: Session = Depends(get_db),
):
    """Re-run the rules engine after inspector field corrections (C-1).

    Keeps the same images/OCR/extraction; re-evaluates applicability + rules
    against the (possibly corrected) extracted fields.
    """
    insp = db.get(Inspection, inspection_id)
    if not insp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    if insp.status not in ("ready_for_review", "reviewed"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Re-assess only after processing (status={insp.status})")

    log_audit(db, "reassess_start", "inspection", entity_id=insp.public_id, actor=user)
    db.commit()

    def _run() -> None:
        with SessionLocal() as session:
            process_inspection(session, session.get(Inspection, inspection_id))

    background_tasks.add_task(_run)
    return {"status": "processing", "inspection_id": inspection_id, "public_id": insp.public_id}