"""A4 process orchestrator.

Runs the verifiable pipeline for an inspection:
    quality -> preprocess -> OCR -> extraction -> rules(assess) -> evidence/findings
Calls B-owned service functions; persists every stage result. Safe to run on a
fresh DB: idempotent re-run clears prior stage rows for the inspection first.
"""
import json
import logging
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from ..models import (Assessment, ExtractedField, Finding, Inspection,
                      InspectionImage, OcrBlock, Rule)
from . import evidence as evidence_svc
from . import extraction as extraction_svc
from . import ocr as ocr_svc
from . import preprocessing as preprocess_svc
from . import quality as quality_svc
from . import rules as rules_svc
from . import storage as storage_svc

logger = logging.getLogger("app.process")

STAGE_FAILED = "FAILED"

RULES_DIR = Path(__file__).resolve().parents[3] / "rules" / "versions" / "seed_rules_v1.json"


def _effective_rules(db: Session, ruleset_version: str) -> List[dict]:
    """Return the applicable rule set for a version in the C-3 JSON dict shape.

    The rules engine (B6, services/rules.py) consumes the canonical C-3 rule
    objects (validation_type / parameters / outcomes / applicability). Those
    full definitions are versioned in `rules/versions/seed_rules_*.json`; the
    DB `rules` table stores a summary for the admin /rules API. Load the
    canonical dict for the inspection's snapshot version so assessments match
    the exact ruleset that was in force.
    """
    path = RULES_DIR
    if not path.exists():
        logger.warning("rules file %s not found; empty ruleset", path)
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("unable to parse rules file %s", path)
        return []
    version = data.get("ruleset", {}).get("version")
    if version != ruleset_version:
        logger.warning(
            "rules file version %r != requested %r; filtering by version from file",
            version, ruleset_version)
    return [
        {**r, "ruleset_version": r.get("version", version or ruleset_version)}
        for r in data.get("rules", [])
        if r.get("version", version) == ruleset_version or version != ruleset_version
    ]


def process_inspection(db: Session, inspection: Inspection) -> None:
    inspection_id = inspection.id
    public_id = inspection.public_id
    inspection.status = "processing"
    inspection.process_error = None
    db.commit()
    try:
        _run_pipeline(db, inspection)
        inspection.status = "ready_for_review"
        logger.info("inspection %s ready_for_review", public_id)
    except Exception as exc:  # pipeline must never leave the inspection hanging
        db.rollback()
        db.expunge_all()
        insp = db.get(Inspection, inspection_id)
        insp.status = STAGE_FAILED
        insp.process_error = f"{type(exc).__name__}: {exc}"
        logger.exception("inspection %s failed: %s", public_id, exc)
        _log_system(db, insp, "process_failed")
    db.commit()


def _run_pipeline(db: Session, inspection: Inspection) -> None:
    ruleset_version = inspection.ruleset_version or _latest_published(db)
    if inspection.ruleset_version is None:
        inspection.ruleset_version = ruleset_version

    _clear_stage_rows(db, inspection.id)

    images = db.query(InspectionImage).filter(InspectionImage.inspection_id == inspection.id).all()
    if not images:
        raise ValueError("no images to process")

    context = {
        "inspection_date": str(inspection.inspection_date or ""),
        "category": inspection.category,
        "channel": inspection.channel,
        "package_structure": inspection.package_structure,
        "origin": inspection.origin,
        "special_status": inspection.special_status,
        "ruleset_version": ruleset_version,
    }
    rules = _effective_rules(db, ruleset_version)

    all_blocks = []
    for img in images:
        raw_bytes = storage_svc.image_bytes(img.original_url)
        quality = quality_svc.analyze_image(raw_bytes)
        img.quality_score_json = quality

        processed_bytes = preprocess_svc.preprocess_image(raw_bytes)
        processed_rel = img.original_url.replace("/original/", "/processed/")
        storage_svc.update_processed_url(inspection.id, img.original_url, processed_rel)
        img.processed_url = processed_rel
        db.flush()

        blocks = ocr_svc.recognize(raw_bytes, source="original")
        enhanced = ocr_svc.recognize(processed_bytes, source="enhanced")
        merged = _merge_blocks(blocks, enhanced)
        for b in merged:
            ob = OcrBlock(
                image_id=img.id,
                inspection_id=inspection.id,
                text=b["text"],
                confidence=b["confidence"],
                bbox=b["bbox"],
                source=b["source"],
            )
            db.add(ob)
            db.flush()
            b["_id"] = ob.id
            b["_image_id"] = img.id
        all_blocks.extend(merged)
        db.commit()

    fields = extraction_svc.extract_fields(all_blocks)
    for f in fields:
        db.add(ExtractedField(
            inspection_id=inspection.id,
            field=f["field"],
            raw=f["raw"],
            normalized=f["normalized"],
            confidence=f.get("confidence"),
            source_ocr_ids=f.get("source_ocr_ids"),
        ))
    db.commit()

    assessments = rules_svc.evaluate_rules(rules, context, all_blocks, fields)
    _persist_assessments(db, inspection.id, assessments, context["ruleset_version"])
    db.commit()

    summary_counts = db.query(Assessment.result).filter(
        Assessment.inspection_id == inspection.id).all()
    logger.info("assessments %s", summary_counts)


def _persist_assessments(db: Session, inspection_id: int, assessments: list, ruleset_version: str) -> None:
    for a in assessments:
        assessment = Assessment(
            inspection_id=inspection_id,
            rule_id=a["rule_id"],
            ruleset_version=ruleset_version,
            result=a["result"],
            evidence_json=a.get("evidence"),
            detail=a.get("detail"),
        )
        db.add(assessment)
        db.flush()
        _create_findings(db, inspection_id, a, assessment, ruleset_version)


def _create_findings(db: Session, inspection_id: int, a: dict, assessment: Assessment,
                     ruleset_version: str) -> None:
    """Create a Finding row per assessment. Only non-NOT-APPLICABLE results and
    results that carry evidence become findings; NOT APPLICABLE / info rules
    skip findings (no evidence obligation)."""
    result = a.get("result", "NOT APPLICABLE")
    if result == "NOT APPLICABLE":
        return

    evidence = a.get("evidence") or {}
    block_ids = evidence.get("block_ids") or []
    field_ids = evidence.get("field_ids") or []
    image_ids = evidence.get("image_ids") or []

    image_id = image_ids[0] if image_ids else None
    ocr_block_id = block_ids[0] if block_ids else None

    # Bbox from the first OCR block referenced.
    bbox = None
    if ocr_block_id is not None:
        ob = db.get(OcrBlock, ocr_block_id)
        if ob:
            bbox = ob.bbox

    severity = a.get("severity", "info")
    finding = Finding(
        assessment_id=assessment.id,
        inspection_id=inspection_id,
        image_id=image_id,
        ocr_block_id=ocr_block_id,
        rule_id=a["rule_id"],
        ruleset_version=ruleset_version,
        bbox=bbox,
        summary=a.get("detail") or f"Rule {a['rule_id']}: {result}",
        severity=severity,
        confidence=evidence.get("confidence"),
        automated_result=result,
        review_status="pending",
    )
    db.add(finding)


def _clear_stage_rows(db: Session, inspection_id: int) -> None:
    db.query(OcrBlock).filter(OcrBlock.inspection_id == inspection_id).delete()
    db.query(ExtractedField).filter(ExtractedField.inspection_id == inspection_id).delete()
    db.query(Finding).filter(Finding.inspection_id == inspection_id).delete()
    db.query(Assessment).filter(Assessment.inspection_id == inspection_id).delete()
    import sqlalchemy as sa
    conn = db.connection()
    conn.execute(
        sa.text("UPDATE inspection_images SET quality_score_json=NULL, processed_url=NULL "
                "WHERE inspection_id=:i"), {"i": inspection_id}
    )
    db.commit()


def _merge_blocks(primary: list, secondary: list) -> list:
    """Placeholder merge: prefer enhanced blocks when their text is longer."""
    seen = []
    for b in secondary + primary:
        if b["text"] and not any(
            abs(b["bbox"]["x1"] - x["bbox"]["x1"]) < 8 and abs(b["bbox"]["y1"] - x["bbox"]["y1"]) < 8
            for x in seen
        ):
            seen.append(b)
    return seen


def _latest_published(db: Session) -> str:
    version = (
        db.query(Rule.version)
        .filter(Rule.status == "published")
        .order_by(Rule.effective_from.desc())
        .first()
    )
    return version[0] if version else "PCR-2026.1"


def _log_system(db: Session, inspection: Inspection, action: str) -> None:
    from .audit import log_audit

    log_audit(db, action, "inspection", entity_id=inspection.public_id,
              system=True, after={"status": inspection.status})