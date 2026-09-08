"""B-OWNED service: evidence builder (replaces placeholder).

Builds the evidence linkage per PRD §22 binding assessment/finding to
image + bbox + OCR span + rule version + confidence. Every finding carrying
evidence MUST reference at least one of: image_id+bbox, ocr_block_id, or
extracted_field_id (C-5 evidence-first rule).
"""
import logging

logger = logging.getLogger("app.evidence")


def build_evidence(block_ids=None, field_ids=None, image_ids=None, confidence=None,
                   bboxes=None) -> dict:
    """Build an evidence dict. bboxes: optional dict mapping block_id -> bbox."""
    block_ids = block_ids or []
    field_ids = field_ids or []
    image_ids = image_ids or []

    evidence = {
        "block_ids": [int(b) for b in block_ids if b is not None],
        "field_ids": [int(f) for f in field_ids if f is not None],
        "image_ids": [int(i) for i in image_ids if i is not None],
        "confidence": round(float(confidence), 4) if confidence is not None else None,
    }
    if bboxes:
        evidence["bboxes"] = {
            str(k): v for k, v in bboxes.items() if v
        }
    return evidence


def has_evidence(evidence: dict) -> bool:
    """C-5 evidence-first: finding is invalid without at least one link."""
    if not isinstance(evidence, dict):
        return False
    return bool(
        (evidence.get("block_ids") or [])
        or (evidence.get("field_ids") or [])
        or (evidence.get("image_ids") or [])
    )


def merge_evidence(*evidence_dicts) -> dict:
    """Combine multiple evidence dicts into a single union."""
    blocks, fields, images = [], [], []
    confidence_values = []
    for ev in evidence_dicts:
        if not ev:
            continue
        blocks.extend(ev.get("block_ids") or [])
        fields.extend(ev.get("field_ids") or [])
        images.extend(ev.get("image_ids") or [])
        c = ev.get("confidence")
        if c is not None:
            confidence_values.append(float(c))

    blocks = _uniq(blocks)
    fields = _uniq(fields)
    images = _uniq(images)
    confidence = round(sum(confidence_values) / len(confidence_values), 4) if confidence_values else None
    return build_evidence(blocks, fields, images, confidence)


def _uniq(seq):
    seen = []
    for x in seq:
        if x not in seen:
            seen.append(x)
    return seen


def validate_finding(evidence: dict) -> tuple:
    """Return (ok, message). A finding with no evidence is rejected."""
    if not has_evidence(evidence):
        return False, "finding has no evidence link (C-5 evidence-first rule)"
    return True, "ok"
