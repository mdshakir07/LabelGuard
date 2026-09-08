"""C-OWNED service: report generation (PDF + docx).

Generates a professional inspection report per PRD §33. Includes header,
inspection metadata, extracted fields, and findings with automated results
(never transformed into legal conclusions).
"""
import io
from datetime import datetime


def _rows_context(inspection, rows: list) -> list:
    """Normalize rows into a list of dicts for rendering."""
    norm = []
    for r in rows:
        if isinstance(r, dict):
            norm.append(r)
        else:
            norm.append({"text": str(r)})
    return norm


def generate_pdf(inspection, rows: list) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                        Table, TableStyle)
    except Exception:
        text = (f"LabelGuard Report\nInspection: {inspection.public_id}\n\n"
                + "\n".join(str(r) for r in rows)
                + "\n\nDisclaimer: This report contains automated findings only and does "
                  "not constitute a legal conclusion. Human confirmation required "
                  "before enforcement action is taken.")
        return text.encode("utf-8")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontSize=20,
                                 textColor=colors.HexColor("#1d4ed8"))
    sub_style = ParagraphStyle("SubTitle", parent=styles["Normal"], fontSize=10,
                               textColor=colors.grey)

    story = []
    story.append(Paragraph("LabelGuard — Inspection Report", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Public ID: {inspection.public_id}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"Status: {inspection.status}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"Inspection date: {inspection.inspection_date}", sub_style))
    story.append(Paragraph(
        f"Channel: {inspection.channel}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"Category: {inspection.category or 'n/a'}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"Origin: {inspection.origin}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"Package structure: {inspection.package_structure}", sub_style))
    if getattr(inspection, "ruleset_version", None):
        story.append(Paragraph(f"Ruleset version: {inspection.ruleset_version}", sub_style))
    story.append(Spacer(1, 12))

    # Header table: metadata
    meta = Table([
        ["Inspection ID", inspection.public_id],
        ["Inspector", getattr(getattr(inspection, "inspector", None), "name", "")],
        ["Location", inspection.location or ""],
    ], colWidths=[40 * mm, 100 * mm])
    meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff6ff")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(meta)
    story.append(Spacer(1, 12))

    # Findings
    rows = _rows_context(inspection, rows)

    # Separate assessments/findings if present in inspection
    assessments = getattr(inspection, "assessments", None)

    if assessments is not None and len(assessments) > 0:
        story.append(Paragraph("Automated Assessments", styles["Heading2"]))
        story.append(Spacer(1, 4))
        data = [["Rule", "Reference", "Result"]]
        for a in assessments:
            data.append([
                str(a.rule_id),
                getattr(a, "rule_number", None) or "",
                str(a.result),
            ])
        assessment_table = Table(data, colWidths=[50 * mm, 40 * mm, 60 * mm])
        assessment_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(assessment_table)
        story.append(Spacer(1, 12))

    if rows:
        story.append(Paragraph("Details", styles["Heading2"]))
        story.append(Spacer(1, 4))
        data = [["#", "Rule", "Result", "Detail"]]
        for i, r in enumerate(rows, 1):
            if isinstance(r, dict):
                data.append([
                    str(i),
                    str(r.get("rule_id", "")),
                    str(r.get("result", "")),
                    (r.get("detail") or r.get("text") or "")[:220],
                ])
            else:
                data.append([str(i), "", "", str(r)[:220]])
        detail_table = Table(data, colWidths=[10 * mm, 40 * mm, 45 * mm, 65 * mm])
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("WORDWRAP", (3, 1), (-1, -1), "CJK"),
        ]))
        story.append(detail_table)

    # Disclaimer
    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Disclaimer: This report contains automated PASS / POTENTIAL NON-COMPLIANCE / "
        "NEEDS VERIFICATION / NOT APPLICABLE findings only. It does not constitute a "
        "legal conclusion. Findings require human confirmation by a competent reviewer "
        "before any enforcement action is taken.",
        ParagraphStyle("Disc", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey)))

    doc.build(story)
    return buf.getvalue()


def generate_docx(inspection, rows: list) -> bytes:
    try:
        from docx import Document
        from docx.shared import Pt
    except Exception:
        return generate_pdf(inspection, rows)

    doc = Document()

    h = doc.add_heading("LabelGuard — Inspection Report", level=0)
    h.alignment = 1

    p = doc.add_paragraph()
    p.add_run(f"Public ID: {inspection.public_id}   Status: {inspection.status}\n")
    p.add_run(f"Inspection date: {inspection.inspection_date}   Channel: {inspection.channel}\n")
    p.add_run(f"Category: {inspection.category or 'n/a'}   Origin: {inspection.origin}")
    if getattr(inspection, "ruleset_version", None):
        p.add_run(f"\nRuleset version: {inspection.ruleset_version}")

    assessments = getattr(inspection, "assessments", None)
    if assessments is not None and len(assessments) > 0:
        doc.add_heading("Automated Assessments", level=1)
        table = doc.add_table(rows=1, cols=3)
        table.style = "Light Grid"
        hdr = table.rows[0].cells
        hdr[0].text, hdr[1].text, hdr[2].text = "Rule", "Reference", "Result"
        for a in assessments:
            row = table.add_row().cells
            row[0].text = str(a.rule_id)
            row[1].text = getattr(a, "rule_number", "") or ""
            row[2].text = str(a.result)

    for r in _rows_context(inspection, rows):
        text = r.get("detail") or r.get("text") or ""
        doc.add_heading(f"{r.get('rule_id', '')} — {r.get('result', '')}", level=2)
        doc.add_paragraph(text)

    doc.add_paragraph(
        "Disclaimer: This report contains automated findings only and does not "
        "constitute a legal conclusion. Human confirmation required before enforcement.")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generate_report(inspection, rows: list, format: str = "pdf") -> bytes:
    if format == "docx":
        return generate_docx(inspection, rows)
    return generate_pdf(inspection, rows)
