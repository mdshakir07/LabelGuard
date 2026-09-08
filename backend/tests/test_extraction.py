"""Unit tests for field extraction + normalization (C-4, B4).

Covers MRP (§14), net quantity (§15), unit sale price (§13), dates and
contact normalizers. Raw OCR is always preserved; normalized may be None.
"""
import pytest

from app.services import extraction as ex


def _block(text, confidence=0.95, _id=1) -> dict:
    return {"text": text, "confidence": confidence, "_id": _id,
            "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 10}}


class TestNormalizers:
    def test_mrp_amount_and_tax_inclusive(self):
        norm = ex._normalize_mrp("MRP (incl. of all taxes) Rs. 129.75")
        assert norm["amount"] == 129.75
        assert norm["currency"] == "INR"
        assert norm["tax_inclusive"] is True

    def test_mrp_no_currency_still_parses(self):
        norm = ex._normalize_mrp("MRP 45")
        assert norm["amount"] == 45.0
        assert norm["currency"] is None

    def test_net_qty_grams_canonical(self):
        norm = ex._normalize_qty("Net Wt. 500 g")
        assert norm["value"] == 500.0
        assert norm["unit"] == "g"
        assert norm["canonical_unit"] == "g"
        assert norm["canonical_value"] == 500.0

    def test_net_qty_kg_to_grams(self):
        norm = ex._normalize_qty("Net Weight 1.5 kg")
        assert norm["canonical_unit"] == "g"
        assert norm["canonical_value"] == 1500.0

    def test_net_qty_litres_to_ml(self):
        norm = ex._normalize_qty("Net Content 2 L")
        assert norm["canonical_unit"] == "ml"
        assert norm["canonical_value"] == 2000.0

    def test_unit_price_per_kg(self):
        norm = ex._normalize_unit_price("Unit price Rs. 250 per kg")
        assert norm["price"] == 250.0
        assert norm["basis"] == "per_kg"

    def test_unit_price_per_100g(self):
        norm = ex._normalize_unit_price("Rs. 20 per 100 g")
        assert norm["basis"] == "per_100g"

    def test_manufacture_date_month_year(self):
        norm = ex._normalize_date("Mfd. JAN 2026")
        assert norm["month"] == 1
        assert norm["year"] == 2026

    def test_ddmmyyyy_date(self):
        norm = ex._normalize_date("Best before 15/08/2027")
        assert norm["month"] == 8
        assert norm["year"] == 2027

    def test_phone_10_digit(self):
        norm = ex._normalize_phone("Toll free: 18001234567")
        assert norm is not None

    def test_email(self):
        norm = ex._normalize_email("Write to consumer.care@mitra.in")
        assert norm == {"email": "consumer.care@mitra.in"}

    def test_country_made_in(self):
        norm = ex._normalize_country("Made in China")
        assert norm == {"country": "China"}


class TestExtraction:
    def test_extracts_numeric_fields_with_normalization(self):
        blocks = [
            _block("Net Wt. 500 g", confidence=0.98, _id=1),
            _block("MRP (incl. of all taxes) Rs. 129.75", confidence=0.99, _id=2),
            _block("Mfd. by Mitra Foods Pvt. Ltd., Mumbai", confidence=0.97, _id=3),
        ]
        fields = ex.extract_fields(blocks)
        by_name = {f["field"]: f for f in fields}
        assert "net_quantity" in by_name
        assert by_name["net_quantity"]["normalized"]["canonical_value"] == 500.0
        assert by_name["net_quantity"]["normalized"]["unit"] == "g"
        assert "mrp" in by_name
        assert by_name["mrp"]["normalized"]["amount"] == 129.75
        assert "manufacturer_name" in by_name
        assert by_name["manufacturer_name"]["raw"] == "Mfd. by Mitra Foods Pvt. Ltd., Mumbai"

    def test_raw_always_preserved_for_unparseable(self):
        # A field hint matched but the normalizer cannot produce a value.
        blocks = [_block("MRP ???", confidence=0.6, _id=1)]
        fields = ex.extract_fields(blocks)
        assert any(f["field"] == "mrp" for f in fields)
        mrp = next(f for f in fields if f["field"] == "mrp")
        assert mrp["raw"] == "MRP ???"

    def test_low_score_blocks_ignored(self):
        blocks = [_block("some unrelated prose about taxes", confidence=0.99, _id=99)]
        fields = ex.extract_fields(blocks)
        assert not any(f["field"] == "mrp" for f in fields)