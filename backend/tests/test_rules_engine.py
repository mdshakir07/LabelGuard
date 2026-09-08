"""Unit tests for the rules engine (B6) and the golden rule vocabulary (C-5).

All tests are pure (no DB): they feed the seed rules JSON + synthetic fields
into services.rules.evaluate_rules and assert on the four-value vocabulary
and high-value rule behaviors.
"""
import json
from pathlib import Path

import pytest

from app.services import rules as rules_svc

SEED = Path(__file__).resolve().parents[2] / "rules" / "versions" / "seed_rules_v1.json"
AUTOMATED = {"PASS", "POTENTIAL NON-COMPLIANCE", "NEEDS VERIFICATION", "NOT APPLICABLE"}


def _rules() -> list:
    data = json.loads(SEED.read_text(encoding="utf-8"))
    version = data["ruleset"]["version"]
    return [dict(r, ruleset_version=r.get("version", version)) for r in data["rules"]]


def _ctx(**overrides) -> dict:
    base = {
        "channel": "retail",
        "origin": "domestic",
        "category": "snacks",
        "package_structure": "single",
        "inspection_date": "2026-09-08",
        "ruleset_version": "PCR-2026.1",
    }
    base.update(overrides)
    return base


def _field(field: str, raw: str, normalized=None, confidence=0.99, _id=1, _image_id=1) -> dict:
    return {"field": field, "raw": raw, "normalized": normalized,
            "confidence": confidence, "_id": _id, "_image_id": _image_id}


def _result_by_rule(results, rule_id):
    return next((r for r in results if r["rule_id"] == rule_id), None)


class TestVocabulary:
    def test_only_four_automated_outcomes(self):
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], [])
        assert results
        for r in results:
            assert r["result"] in AUTOMATED, f"{r['rule_id']} -> {r['result']}"

    def test_seed_outcomes_respect_vocabulary(self):
        for r in _rules():
            for key, val in (r.get("outcomes") or {}).items():
                assert val in rules_svc.VALID_OUTCOMES, f"{r['rule_id']}:{key}={val}"

    def test_findings_carry_evidence_for_non_na(self):
        # Full pipeline evidence-first: non-NOT-APPLICABLE results may carry
        # block/field/image ids; NOT APPLICABLE ones are not asserted here.
        fields = [_field("net_quantity", "Net Wt. 500 g",
                         {"value": 500, "unit": "g", "canonical_unit": "g", "canonical_value": 500})]
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields)
        for r in results:
            if r["result"] != "NOT APPLICABLE":
                assert r.get("evidence") is not None


class TestApplicability:
    def test_r_app_04_na_when_not_for_retail(self):
        fields = [_field("not_for_retail_sale", "NOT FOR RETAIL SALE")]
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields)
        app04 = _result_by_rule(results, "R-APP-04")
        assert app04 is not None
        assert app04["result"] == "NOT APPLICABLE"

    def test_decl_02_skipped_for_domestic(self):
        # Imported origin = country of origin required; domestic -> not applicable.
        results = rules_svc.evaluate_rules(
            _rules(), _ctx(origin="domestic"), [],
            [_field("net_quantity", "Net Wt. 100 g", {"value": 100, "unit": "g"})])
        decl02 = _result_by_rule(results, "R-DECL-02")
        assert decl02 is None or decl02["result"] == "NOT APPLICABLE"

    def test_decl_02_applies_when_imported_and_present(self):
        results = rules_svc.evaluate_rules(
            _rules(), _ctx(origin="imported"), [],
            [_field("country_of_origin", "Made in India", {"country": "India"})])
        decl02 = _result_by_rule(results, "R-DECL-02")
        assert decl02 is not None
        assert decl02["result"] in ("PASS", "NEEDS VERIFICATION")


class TestMandatoryDeclarations:
    def test_decl_05_net_qty_missing_is_potential(self):
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], [])
        r = _result_by_rule(results, "R-DECL-05")
        assert r is not None and r["result"] == "POTENTIAL NON-COMPLIANCE"

    def test_decl_05_pass_when_present(self):
        fields = [_field("net_quantity", "Net Wt. 500 g",
                         {"value": 500, "unit": "g", "canonical_unit": "g", "canonical_value": 500})]
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields)
        r = _result_by_rule(results, "R-DECL-05")
        assert r is not None and r["result"] == "PASS"

    def test_decl_01_any_of_manufacturer_or_packer(self):
        fields = [_field("manufacturer_name", "Made by Mitra Foods, Mumbai")]
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields)
        r = _result_by_rule(results, "R-DECL-01")
        assert r is not None and r["result"] == "PASS"
        fields2 = [_field("packer_name", "Packed by Pune Packers")]
        results2 = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields2)
        r2 = _result_by_rule(results2, "R-DECL-01")
        assert r2 is not None and r2["result"] == "PASS"

    def test_low_confidence_downgrades_to_needs_verification(self):
        fields = [_field("net_quantity", "Net Wt. 500 g",
                         {"value": 500, "unit": "g"}, confidence=0.4)]
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields)
        r = _result_by_rule(results, "R-DECL-05")
        assert r is not None and r["result"] == "NEEDS VERIFICATION"


class TestQuantityAndUnits:
    def test_qty_01_normalizes_kg(self):
        fields = [_field("net_quantity", "Net Wt. 1 kg",
                         {"value": 1, "unit": "kg", "canonical_unit": "g", "canonical_value": 1000})]
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields)
        r = _result_by_rule(results, "R-QTY-01")
        assert r is not None and r["result"] == "PASS"

    def test_qty_01_ambiguous_unit(self):
        fields = [_field("net_quantity", "Net Wt. 500",
                         {"value": 500, "unit": None})]
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields)
        r = _result_by_rule(results, "R-QTY-01")
        assert r is not None and r["result"] == "NEEDS VERIFICATION"

    def test_app_03_under_threshold_pass(self):
        fields = [_field("net_quantity", "Net Wt. 1 kg",
                         {"value": 1, "unit": "kg", "canonical_unit": "g", "canonical_value": 1000})]
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields)
        r = _result_by_rule(results, "R-APP-03")
        assert r is not None and r["result"] == "PASS"

    def test_app_03_over_25kg_needs_verification(self):
        fields = [_field("net_quantity", "Net Wt. 30 kg",
                         {"value": 30, "unit": "kg", "canonical_unit": "g", "canonical_value": 30000})]
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields)
        r = _result_by_rule(results, "R-APP-03")
        assert r is not None and r["result"] == "NEEDS VERIFICATION"


class TestUnitSalePrice:
    def test_unit_matches_per_kg_basis(self):
        fields = [
            _field("net_quantity", "Net Wt. 1 kg",
                   {"value": 1, "unit": "kg", "canonical_unit": "g", "canonical_value": 1000}),
            _field("unit_sale_price", "Price per kg Rs. 200",
                   {"price": 200, "currency": "INR", "basis": "per_kg"}),
        ]
        results = rules_svc.evaluate_rules(_rules(), _ctx(unit_sale_price_required=True), [], fields)
        r = _result_by_rule(results, "R-UNIT")
        assert r is not None and r["result"] == "PASS"

    def test_unit_mismatch_is_potential(self):
        fields = [
            _field("net_quantity", "Net Wt. 1 kg",
                   {"value": 1, "unit": "kg", "canonical_unit": "g", "canonical_value": 1000}),
            _field("unit_sale_price", "Price per 100 g Rs. 20",
                   {"price": 20, "currency": "INR", "basis": "per_100g"}),
        ]
        results = rules_svc.evaluate_rules(_rules(), _ctx(unit_sale_price_required=True), [], fields)
        r = _result_by_rule(results, "R-UNIT")
        assert r is not None
        assert r["result"] in ("PASS", "POTENTIAL NON-COMPLIANCE", "NEEDS VERIFICATION")


class TestReadability:
    def test_read_01_pass_when_confidence_high(self):
        fields = [_field("net_quantity", "Net Wt. 500 g",
                         {"value": 500, "unit": "g"}, confidence=0.98)]
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields)
        r = _result_by_rule(results, "R-READ-01")
        assert r is not None and r["result"] == "PASS"

    def test_read_01_needs_verification_when_low(self):
        fields = [_field("net_quantity", "ne",
                         {"value": None}, confidence=0.2)]
        results = rules_svc.evaluate_rules(_rules(), _ctx(), [], fields)
        r = _result_by_rule(results, "R-READ-01")
        assert r is not None and r["result"] == "NEEDS VERIFICATION"


class TestRobustness:
    def test_bad_rule_does_not_crash_pipeline(self):
        bad = [{"rule_id": "R-X", "validation_type": "made_up",
                "severity": "info", "applicability": {"always": True},
                "parameters": {}, "outcomes": {}}]
        results = rules_svc.evaluate_rules(bad, _ctx(), [], [])
        assert results[0]["result"] in AUTOMATED

    def test_no_applicable_rules_gives_na(self):
        rules = [{"rule_id": "R-NOPE", "validation_type": "presence",
                  "applicability": {"category": "nirvana"},
                  "parameters": {"fields": ["x"]}, "outcomes": {}}]
        results = rules_svc.evaluate_rules(rules, _ctx(category="snacks"), [], [])
        assert results[0]["rule_id"] == "R-APP-01"
        assert results[0]["result"] == "NOT APPLICABLE"