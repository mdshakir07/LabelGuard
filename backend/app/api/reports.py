from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.deps import require_or_higher, require_writer
from ..config import get_settings
from ..db import SessionLocal, get_db
from ..models import (Assessment, ExtractedField, Finding, Inspection,
                      Product, Report, User)
from ..services.audit import log_audit
from ..services.reports import generate_docx, generate_pdf

router = APIRouter(prefix="/inspections", tags=["reports"])


class ReportRequest(BaseModel):
    format: str = "pdf"


@router.post("/{inspection_id}/report")
def generate_report(
    inspection_id: int,
    background_tasks: BackgroundTasks,
    body: ReportRequest | None = None,
    user: User = Depends(require_writer),
    db: Session = Depends(get_db),
):
    insp = db.get(Inspection, inspection_id)
    if not insp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    if insp.status == "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot report on a draft inspection")

    fmt = (body.format if body else "pdf").lower()
    if fmt not in ("pdf", "docx"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="format must be pdf|docx")

    rows = _report_rows(db, insp)

    def _write() -> None:
        with SessionLocal() as session:
            s = session.get(Inspection, inspection_id)
            generator = generate_docx if fmt == "docx" else generate_pdf
            content = generator(s, rows)
            rel = f"reports/{s.public_id}.{fmt}"
            root = get_settings().resolved_storage_root
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(content)
            session.add(Report(
                inspection_id=inspection_id,
                format=fmt,
                url=rel,
                size_bytes=len(content),
                generated_by=user.id,
            ))
            session.commit()

    log_audit(db, "report_generate", "inspection", entity_id=insp.public_id, actor=user,
              after={"format": fmt})
    db.commit()
    background_tasks.add_task(_write)
    return {
        "status": "generating",
        "inspection_id": inspection_id,
        "public_id": insp.public_id,
        "format": fmt,
    }


@router.get("/{inspection_id}/report")
def get_report(
    inspection_id: int,
    fmt: str = "pdf",
    user: User = Depends(require_or_higher("inspector")),
    db: Session = Depends(get_db),
):
    rep = (
        db.query(Report)
        .filter(Report.inspection_id == inspection_id)
        .order_by(Report.created_at.desc())
        .first()
    )
    if not rep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not generated yet")
    if fmt not in ("pdf", "docx"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="format must be pdf|docx")
    root = get_settings().resolved_storage_root
    path = (root / rep.url).resolve()
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file missing")
    media = "application/pdf" if rep.url.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(str(path), media_type=media, filename=Path(rep.url).name)


def _report_rows(db: Session, insp: Inspection) -> list:
    rows = [f"Meta: {insp.public_id} | {insp.channel} | {insp.inspection_date} | ruleset {insp.ruleset_version}"]
    for f in db.query(ExtractedField).filter(ExtractedField.inspection_id == insp.id).all():
        rows.append(f"Field {f.field}: raw={f.raw} normalized={f.normalized} conf={f.confidence}")
    for a in db.query(Assessment).filter(Assessment.inspection_id == insp.id).all():
        rows.append(f"Assessment {a.rule_id}: {a.result} (evidence={bool(a.evidence_json)})")
    for f in db.query(Finding).filter(Finding.inspection_id == insp.id).all():
        rows.append(f"Finding {f.rule_id}: {f.automated_result} | review {f.review_status} | {f.summary}")
    return rows