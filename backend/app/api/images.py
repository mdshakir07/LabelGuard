from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from ..auth.deps import require_or_higher, require_writer
from ..db import get_db
from ..models import Inspection, InspectionImage, User
from ..schemas.inspection import InspectionImageOut
from ..services.audit import log_audit
from ..services.quality import analyze_image
from ..services.storage import image_bytes, validate_and_store
from sqlalchemy.orm import Session

router = APIRouter(prefix="/inspections", tags=["images"])

ALLOWED_TYPES = {"front", "back", "side", "top", "bottom", "closeup", "listing"}


@router.post("/{inspection_id}/images",
             status_code=status.HTTP_201_CREATED)
async def upload_images(
    inspection_id: int,
    files: List[UploadFile] = File(...),
    typ: str = Form("front"),
    user: User = Depends(require_writer),
    db: Session = Depends(get_db),
):
    insp = db.get(Inspection, inspection_id)
    if not insp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspection not found")
    if insp.status != "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Images can only be added to draft inspections (status={insp.status})")
    if typ not in ALLOWED_TYPES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"image type must be one of {sorted(ALLOWED_TYPES)}")

    created: List[InspectionImage] = []
    warnings: List[str] = []
    for f in files:
        contents = await f.read()
        meta = validate_and_store(contents, f.filename or "image", typ, inspection_id)
        # Quality gate at capture time (PRD §23 / S04): warn before processing.
        q = analyze_image(contents)
        for w in q.get("warnings", []):
            prefix = f"{f.filename or 'image'}: {w}" if len(files) > 1 else w
            if prefix not in warnings:
                warnings.append(prefix)
        img = InspectionImage(
            inspection_id=inspection_id,
            type=typ,
            original_url=meta["original_url"],
            sha256=meta["sha256"],
            width=meta["width"],
            height=meta["height"],
            quality_score_json=q,
        )
        db.add(img)
        created.append(img)

    if not created:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No files supplied")

    db.flush()
    log_audit(db, "upload_images", "inspection", entity_id=insp.public_id, actor=user,
              after={"count": len(created), "type": typ, "warnings": warnings})
    db.commit()
    for img in created:
        db.refresh(img)
    return {"created": created, "warnings": warnings}


@router.get("/{inspection_id}/images/{image_id}/file")
def serve_image(
    inspection_id: int,
    image_id: int,
    user: User = Depends(require_or_higher("inspector")),
    db: Session = Depends(get_db),
):
    img = db.query(InspectionImage).filter(
        InspectionImage.id == image_id, InspectionImage.inspection_id == inspection_id).first()
    if not img:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    content = image_bytes(img.original_url)
    return Response(content=content, media_type="image/jpeg")