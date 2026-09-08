"""Tests for quality gate (B1), report generation (C6 service side), and the
process orchestrator's rule-loading helper (A4).
"""
import json

from PIL import Image, ImageDraw, ImageFont

from app.services import reports as reports_svc
from app.services import quality as quality_svc
from app.services.process import RULES_DIR, _effective_rules


def _png_bytes(text: str = "Net Wt. 500 g", size=(900, 520)) -> bytes:
    img = Image.new("RGB", size, (232, 232, 232))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
    except OSError:
        font = ImageFont.load_default()
    d.text((40, 100), text, fill="black", font=font)
    d.text((40, 200), "MRP Rs. 129.75", fill="black", font=font)
    d.text((40, 300), "Made by Mitra Foods, Mumbai", fill="black", font=font)
    out = __import__("io").BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


class TestQuality:
    def test_shape(self):
        result = quality_svc.analyze_image(_png_bytes())
        assert set(result) == {"score", "warnings", "recommendation"}
        assert 0.0 <= result["score"] <= 1.0
        assert isinstance(result["warnings"], list)

    def test_clean_image_scores_high(self):
        # Gray background (not overexposed), >=480px, sharp text -> proceed.
        result = quality_svc.analyze_image(_png_bytes())
        assert result["score"] >= 0.5
        assert result["recommendation"] == "proceed"

    def test_blur_detected(self):
        img = Image.new("RGB", (300, 200), "gray")
        buf = __import__("io").BytesIO()
        img.save(buf, "PNG")
        result = quality_svc.analyze_image(buf.getvalue())
        assert result["warnings"]  # solid gray is low variance -> blur warning

    def test_empty_bytes_handled(self):
        result = quality_svc.analyze_image(b"")
        assert result["score"] is not None


class FakeInspection:
    def __init__(self, public_id, status="ready_for_review", inspection_date="2026-09-08",
                 channel="retail", category="food", origin="domestic",
                 package_structure="single", ruleset_version="PCR-2026.1"):
        self.public_id = public_id
        self.status = status
        self.inspection_date = inspection_date
        self.channel = channel
        self.category = category
        self.origin = origin
        self.package_structure = package_structure
        self.ruleset_version = ruleset_version
        self.location = "New Delhi"
        self.assessments = []


class TestReports:
    def test_pdf_is_valid(self):
        pdf = reports_svc.generate_pdf(
            FakeInspection("IN-2026-0001"),
            [{"rule_id": "R-DECL-05", "result": "PASS", "detail": "Net quantity present"}],
        )
        assert pdf.startswith(b"%PDF")
        assert len(pdf) > 1000  # real content, not empty

    def test_pdf_plaintext_fallback(self, monkeypatch):
        import builtins
        real_import = builtins.__import__

        def _fake_import(name, *a, **k):
            if name.startswith("reportlab"):
                raise ImportError("reportlab unavailable")
            return real_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", _fake_import)
        text = reports_svc.generate_pdf(FakeInspection("IN-2026-0002"), ["dummy row"])
        assert b"LabelGuard Report" in text
        assert b"legal conclusion" in text

    def test_docx_is_zip(self):
        content = reports_svc.generate_docx(
            FakeInspection("IN-2026-0003"),
            [{"rule_id": "R-DECL-05", "result": "PASS", "detail": "ok"}],
        )
        assert content[:2] == b"PK"

    def test_docx_contains_disclaimer(self):
        import io
        import zipfile

        content = reports_svc.generate_docx(
            FakeInspection("IN-2026-0004"),
            [{"rule_id": "R-DECL-05", "result": "PASS", "detail": "ok"}],
        )
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
        assert "legal conclusion" in xml

    def test_report_router_dispatch(self):
        rows = [{"rule_id": "R-READ-01", "result": "PASS", "detail": "legible"}]
        pdf = reports_svc.generate_report(FakeInspection("IN-2026-0005"), rows, "pdf")
        assert pdf.startswith(b"%PDF")
        docx = reports_svc.generate_report(FakeInspection("IN-2026-0005"), rows, "docx")
        assert docx[:2] == b"PK"


class TestRulesLoading:
    def test_effective_rules_reads_seed_json(self):
        assert RULES_DIR.exists(), f"seed file missing: {RULES_DIR}"
        rules = _effective_rules(None, "PCR-2026.1")
        assert len(rules) >= 27
        sample = rules[0]
        # Engine contract shape (C-3): dicts with the get()-based keys.
        for key in ("rule_id", "validation_type", "parameters", "outcomes", "applicability"):
            assert key in sample, f"missing {key}"

    def test_seed_envelope_is_published(self):
        data = json.loads(RULES_DIR.read_text(encoding="utf-8"))
        assert data["ruleset"]["version"] == "PCR-2026.1"
        assert data["ruleset"]["review_status"] == "published"