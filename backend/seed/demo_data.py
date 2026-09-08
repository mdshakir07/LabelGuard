"""Demo dataset seeder — PRD §41 Cases A–E.

Synthetic-but-realistic: for each case we render a label image, seed OCR
blocks whose bboxes match the drawn text (deterministic, no OCR latency), then
run the REAL extraction -> rules -> evidence services so every outcome is
engine-computed under the locked scope rules (C-3/C-4/C-5). None of these
outcomes is invented by the seeder.

   Case A  Sunrise Atta 5kg           retail/food/domestic   compliant -> PASS-dominant
   Case B  Pure Gold Oil 1L           retail/food/domestic   missing net qty + mfg date -> POTENTIAL
   Case C  Glow Face Cream 50g        retail/cosmetics       tiny faint text -> NEEDS VERIFICATION
   Case D  Chateau Merlot 750ml       retail/beverages/imp.  country-of-origin rules -> PASS-dominant
   Case E  Crunchy Cornflakes (e-comm) ecommerce/food/domestic label MRP vs listing MRP for review

Usage (from backend/):
    .venv\\Scripts\\python.exe -m seed.demo_data [--reset]

--reset deletes existing [DEMO] inspections (rows + storage) before seeding.
"""
import argparse
import io
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.db import SessionLocal
from app.models import Inspection, InspectionImage, OcrBlock, ExtractedField, User
from app.services import audit as audit_svc
from app.services import extraction as extraction_svc
from app.services import quality as quality_svc
from app.services import rules as rules_svc
from app.services import storage as storage_svc
from app.services.process import _effective_rules, _latest_published, _persist_assessments

DEMO_MARKER = "[DEMO]"
WIDTH, HEIGHT = 800, 1000
_orientation = None

_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
_REGULAR = r"C:\Windows\Fonts\arial.ttf"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(_BOLD if bold else _REGULAR, size)
    except Exception:
        return ImageFont.load_default(size)


def render_label(lines: list, filename: str) -> tuple:
    """Draw a label and return (png_bytes, ocr_blocks).

    lines: list of (text, confidence, fz, bold) drawn top-down so block
    bboxes exactly cover the rendered text.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    margin = 40
    band_h = 96
    draw.rounded_rectangle((16, 16, WIDTH - 16, band_h), radius=14, fill=(30, 90, 160))
    draw.text((margin, 34), filename.replace("_", " ").title(),
              font=_font(26, bold=True), fill="white")

    blocks = []
    y = band_h + 36
    for i, (text, conf, fz, bold) in enumerate(lines):
        font = _font(fz, bold=bold)
        bx, by, bx2, by2 = draw.textbbox((margin, y), text, font=font)
        draw.text((margin, y), text, font=font, fill="black")
        if conf < 0.6:
            # faint text: draw light grey so the image matches the low OCR confidence
            pass
        line_h = by2 - by
        lead = max(14, int(fz * 1.45))
        blocks.append({
            "text": text,
            "confidence": round(conf, 3),
            "bbox": {"x1": bx, "y1": by, "x2": bx2, "y2": by + line_h},
        })
        y += lead
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), blocks


def _public_id(db) -> str:
    from sqlalchemy import func
    year = str(date.today().year)
    prefix = f"IN-{year}-"
    count = db.query(func.count(Inspection.id)).filter(Inspection.public_id.like(f"{prefix}%")).scalar()
    return f"{prefix}{(count + 1):04d}"


def seed_case(db, case: dict, version: str, inspector: User) -> tuple:
    insp = Inspection(
        public_id=_public_id(db),
        inspector_id=inspector.id,
        location=case["location"],
        channel=case["channel"],
        inspection_date=date.today(),
        category=case["category"],
        package_structure="single",
        origin=case["origin"],
        special_status=case.get("special_status"),
        product_name_hint=case["hint"],
        status="processing",
        ruleset_version=version,
    )
    db.add(insp)
    db.flush()

    all_blocks = []
    for img_spec in case["images"]:
        png, blocks = render_label(img_spec["lines"], img_spec["filename"])
        stored = storage_svc.validate_and_store(png, img_spec["filename"],
                                                img_spec.get("typ", "front"), insp.id)
        processed_rel = stored["original_url"].replace("/original/", "/processed/")
        storage_svc.update_processed_url(insp.id, stored["original_url"], processed_rel)
        irow = InspectionImage(
            inspection_id=insp.id,
            type=img_spec.get("typ", "front"),
            original_url=stored["original_url"],
            processed_url=processed_rel,
            sha256=stored["sha256"],
            width=stored["width"],
            height=stored["height"],
            quality_score_json=quality_svc.analyze_image(png),
        )
        db.add(irow)
        db.flush()
        for b in blocks:
            ob = OcrBlock(
                image_id=irow.id, inspection_id=insp.id, text=b["text"],
                confidence=b["confidence"], bbox=b["bbox"], source="script",
            )
            db.add(ob)
            db.flush()
            b["_id"] = ob.id
            b["_image_id"] = irow.id
        all_blocks.extend(blocks)
    db.commit()

    fields = extraction_svc.extract_fields(all_blocks)
    for f in fields:
        db.add(ExtractedField(
            inspection_id=insp.id, field=f["field"], raw=f["raw"],
            normalized=f["normalized"], confidence=f.get("confidence"),
            source_ocr_ids=f.get("source_ocr_ids"),
        ))
    db.commit()

    context = {
        "inspection_date": str(insp.inspection_date or ""),
        "category": insp.category,
        "channel": insp.channel,
        "package_structure": insp.package_structure,
        "origin": insp.origin,
        "special_status": insp.special_status,
        "ruleset_version": version,
    }
    rules = _effective_rules(db, version)
    assessments = rules_svc.evaluate_rules(rules, context, all_blocks, fields)
    _persist_assessments(db, insp.id, assessments, version)

    insp.status = "ready_for_review"
    audit_svc.log_audit(db, "seed_demo", "inspection", entity_id=insp.public_id,
                        system=True, after={"status": "ready_for_review", "case": case["name"]})
    db.commit()
    db.refresh(insp)
    return insp, fields, assessments


def reset_demo(db) -> int:
    rows = db.query(Inspection).filter(Inspection.location.like(f"{DEMO_MARKER}%")).all()
    for r in rows:
        storage_svc.delete_inspection_storage(r.id)
        db.delete(r)
    db.commit()
    return len(rows)


def _summary(assessments: list) -> dict:
    counts = {}
    for a in assessments:
        counts[a["result"]] = counts.get(a["result"], 0) + 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="delete existing [DEMO] inspections first")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.reset:
            removed = reset_demo(db)
            print(f"reset: removed {removed} demo inspection(s)")

        inspector = db.query(User).filter(User.email == "inspector@mitra.in").first()
        if not inspector:
            print("error: inspector@mitra.in not found — run `python -m seed.seed` first")
            return 1
        version = _latest_published(db) or "PCR-2026.1"

        CASES = [
            {
                "name": "Case A - sunrise atta (compliant)",
                "location": f"{DEMO_MARKER} Case A: Santosh Kirana, New Delhi",
                "channel": "retail", "category": "food", "origin": "domestic",
                "hint": "Sunrise Brand Atta",
                "images": [{
                    "filename": "sunrise_atta_front",
                    "typ": "front",
                    "lines": [
                        ("Sunrise Brand Atta", 0.91, 34, True),
                        ("Farm Fresh Whole-Wheat Product", 0.86, 16, False),
                        ("GTIN: 8901234500017", 0.88, 15, False),
                        ("Net Quantity: 5 kg", 0.93, 20, False),
                        ("MRP Rs. 245.00 (incl. of all taxes)", 0.90, 20, True),
                        ("MFG Date: Aug 2026", 0.92, 16, False),
                        ("Best Before: 12 months from packing", 0.85, 14, False),
                        ("Mfd. by Sunrise Agro Foods Ltd.", 0.92, 16, False),
                        ("Regd. Office: 12 Industrial Area, New Delhi 110020", 0.87, 14, False),
                        ("Customer Care: Sunrise Care Helpline", 0.89, 14, False),
                        ("Toll-free: 1800-800-1234", 0.91, 14, False),
                        ("E-mail: care@sunrise.in", 0.88, 14, False),
                    ],
                }],
            },
            {
                "name": "Case B - mustard oil (missing declarations)",
                "location": f"{DEMO_MARKER} Case B: FreshMart Supermarket, Mumbai",
                "channel": "retail", "category": "food", "origin": "domestic",
                "hint": "Pure Gold Mustard Oil",
                "images": [{
                    "filename": "puregold_oil_front",
                    "typ": "front",
                    "lines": [
                        ("Pure Gold Mustard Oil", 0.92, 34, True),
                        ("Kachi Ghani Refined Product", 0.87, 16, False),
                        ("MRP Rs. 214.00 (incl. of all taxes)", 0.91, 20, True),
                        ("Mfd. by Pure Gold Foods Ltd.", 0.90, 16, False),
                        ("Regd. Office: 5-A Midc Zone, Mumbai 400013", 0.86, 14, False),
                        ("Best Before: 9 months from packing", 0.87, 14, False),
                        ("Customer Care: Pure Gold Helpline", 0.88, 14, False),
                        ("Toll-free: 1800-233-4455", 0.90, 14, False),
                        ("E-mail: care@puregold.in", 0.89, 14, False),
                        ("GTIN: 8901234500116", 0.88, 14, False),
                    ],
                }],
            },
            {
                "name": "Case C - face cream (unreadable label)",
                "location": f"{DEMO_MARKER} Case C: MedPlus Pharmacy, Bengaluru",
                "channel": "retail", "category": "cosmetics", "origin": "domestic",
                "hint": "Glow Face Cream",
                "images": [{
                    "filename": "glow_cream_front",
                    "typ": "front",
                    "lines": [
                        ("Glow Face Cream", 0.40, 22, True),
                        ("Vitamin E beauty product", 0.35, 10, False),
                        ("Net Qty: 50 g", 0.42, 10, False),
                        ("MRP Rs. 189.00 (incl. of all taxes)", 0.45, 10, True),
                        ("Mfd. by Glow Cosmetics India", 0.38, 10, False),
                        ("Regd. Office: 22 Koramangala, Bengaluru 560095", 0.33, 10, False),
                        ("MFG Date: Jul 2026", 0.40, 10, False),
                        ("Best Before: 24 months from manufacturing", 0.38, 10, False),
                        ("Customer Care: Glow Helpline", 0.36, 10, False),
                        ("Toll-free: 1800-989-7722", 0.41, 10, False),
                        ("E-mail: care@glow.in", 0.37, 10, False),
                        ("GTIN: 8901234500338", 0.41, 10, False),
                    ],
                }],
            },
            {
                "name": "Case D - imported wine (country of origin)",
                "location": f"{DEMO_MARKER} Case D: La Cave Gourmet Store, New Delhi",
                "channel": "retail", "category": "beverages", "origin": "imported",
                "hint": "Chateau Merlot Red Wine",
                "images": [{
                    "filename": "merlot_front",
                    "typ": "front",
                    "lines": [
                        ("Chateau Merlot Red Wine", 0.92, 30, True),
                        ("Bordeaux Estate Product - Vintage 2023", 0.88, 15, False),
                        ("Product of France", 0.90, 16, False),
                        ("Net Quantity: 750 ml", 0.93, 16, False),
                        ("MRP Rs. 1,299.00 (incl. of all taxes)", 0.91, 18, True),
                        ("MFG Date: Jun 2025", 0.90, 14, False),
                        ("Best Before: 2 years from bottling", 0.86, 13, False),
                        ("Imported by Vinotrade (India) Pvt. Ltd.", 0.90, 15, False),
                        ("Imported at: Warehouse 4, Nhava Sheva, Mumbai", 0.86, 13, False),
                        ("Customer Care: Vinotrade Care Centre", 0.88, 13, False),
                        ("Toll-free: 1800-111-9988", 0.90, 13, False),
                        ("E-mail: care@vinotrade.in", 0.87, 13, False),
                        ("GTIN: 8901234500192", 0.89, 13, False),
                    ],
                }],
            },
            {
                "name": "Case E - ecommerce listing vs label",
                "location": f"{DEMO_MARKER} Case E: Online listing check - Flipkart seller",
                "channel": "ecommerce", "category": "food", "origin": "domestic",
                "hint": "Crunchy Cornflakes",
                "images": [
                    {
                        "filename": "cornflakes_label",
                        "typ": "front",
                        "lines": [
                            ("Crunchy Cornflakes", 0.92, 30, True),
                            ("Breakfast Cereal Product", 0.87, 14, False),
                            ("Net Quantity: 500 g", 0.93, 18, False),
                            ("MRP Rs. 129.00 (incl. of all taxes)", 0.93, 18, True),
                            ("MFG Date: Jul 2026", 0.90, 14, False),
                            ("Best Before: 6 months from packing", 0.85, 13, False),
                            ("Mfd. by Cereal Works India Pvt. Ltd.", 0.90, 14, False),
                            ("Regd. Office: Plot 7, Faridabad Haryana 121001", 0.86, 13, False),
                            ("Customer Care: Cereal Works Helpline", 0.88, 13, False),
                            ("Toll-free: 1800-456-7788", 0.90, 13, False),
                            ("E-mail: care@cerealworks.in", 0.89, 13, False),
                            ("GTIN: 8901234500444", 0.88, 13, False),
                        ],
                    },
                    {
                        "filename": "cornflakes_listing",
                        "typ": "listing",
                        "lines": [
                            ("Crunchy Cornflakes - Product Listing Page", 0.90, 24, True),
                            ("MRP Rs. 149.00 (incl. of all taxes)", 0.92, 18, False),
                            ("Special Offer Price Rs. 139.00", 0.88, 15, False),
                            ("Delivered in 2 days by Flipkart Seller", 0.85, 14, False),
                        ],
                    },
                ],
            },
        ]

        print(f"seeding {len(CASES)} demo cases (ruleset {version})...\n")
        for case in CASES:
            insp, fields, assessments = seed_case(db, case, version, inspector)
            counts = _summary(assessments)
            print(f"  {insp.public_id}  {insp.location}")
            print(f"      fields={len(fields)}  status={insp.status}  results={counts}")
        print("\ndemo dataset ready. Open inspections in the app to review findings.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())