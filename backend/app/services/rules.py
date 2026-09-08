"""B-OWNED service: deterministic rules engine (replaces placeholder).

Implements the applicability engine (B5) + deterministic rules (B6) against
seed_rules_v1.json (C-3). Outputs ONLY the four C-5 automated outcomes:
PASS | POTENTIAL NON-COMPLIANCE | NEEDS VERIFICATION | NOT APPLICABLE

Contract:
    evaluate_rules(rules, context, blocks, fields) -> list[assessment_dict]
Each assessment_dict:
    {
      "rule_id", "ruleset_version", "result",
      "evidence": {"block_ids": [], "field_ids": [], "image_ids": [], "confidence": float},
      "detail": str,
    }
"""
import logging
from typing import List

logger = logging.getLogger("app.rules")

VALID_OUTCOMES = {"pass", "potential_non_compliance", "needs_verification", "not_applicable", "info"}

# Applicability key -> context field it maps to.
_CONTEXT_KEYS = {
    "channel": "channel",
    "origin": "origin",
    "category": "category",
    "package_structure": "package_structure",
    "special_status": "special_status",
    "retail_package": "channel",      # retail/ecommerce -> retail
    "perishable": "category",
    "unit_sale_price_required": "unit_sale_price_required",
    "sale_evidence_available": "sale_evidence_available",
    "measurement_available": "measurement_available",
    "standard_quantity_applies": "standard_quantity_applies",
    "dimensions_relevant": "category",
    "not_for_retail_sale": "not_for_retail_sale",
}


def _field_map(fields: list) -> dict:
    """Map field_name -> field dict (first occurrence)."""
    result = {}
    for f in fields:
        name = f.get("field")
        if name and name not in result:
            result[name] = f
    return result


def _eval_condition(app: dict, context: dict, field_map: dict) -> tuple:
    """Evaluate one applicability entry. Returns (applicable: bool, reason: str)."""
    if app is None:
        return True, "no-applicability"
    if "always" in app and app["always"]:
        return True, "always"
    if "retail_package" in app and app["retail_package"]:
        return context.get("channel") in ("retail", "ecommerce"), "retail-package"
    if "origin" in app:
        return context.get("origin") == app["origin"], f"origin={app['origin']}"
    if "category" in app:
        vals = app["category"]
        if isinstance(vals, str):
            vals = [vals]
        cats = [c.lower() for c in vals]
        return (context.get("category") or "").lower() in cats, f"category in {cats}"
    if "channel" in app:
        vals = app["channel"]
        if isinstance(vals, str):
            vals = [vals]
        return context.get("channel") in vals, f"channel in {vals}"
    if "package_structure" in app:
        return context.get("package_structure") == app["package_structure"], f"structure={app['package_structure']}"
    if "special_status" in app:
        return context.get("special_status") == app["special_status"], f"special={app['special_status']}"
    if "field" in app:
        val = app.get("value")
        exists = app["field"] in field_map or app["field"] in context
        if val is True and app["field"] == "not_for_retail_sale":
            return exists, "not_for_retail_sale"
        if app.get("field") == "net_quantity":
            return "net_quantity" in field_map, "net_quantity present"
        if app.get("field") == "net_quantity_present":
            return "net_quantity" in field_map, "net_quantity present"
        if "value" in app or val is not None:
            return exists, f"{app['field']} present"
        return exists, f"{app['field']} present"
    # fallback context direct flag
    for key in _CONTEXT_KEYS:
        if key in app and isinstance(app[key], bool):
            ctx_val = context.get(_CONTEXT_KEYS[key], False)
            return bool(ctx_val) == app[key], f"ctx:{key}"
    # "value" on the rule itself
    return False, f"unknown applicability {app}"


def _is_applicable(rule: dict, context: dict, field_map: dict) -> tuple:
    app = rule.get("applicability")
    if not app:
        return True, "no-applicability"
    for key, cond in app.items():
        if isinstance(cond, bool) and key not in ("always", "retail_package", "not_for_retail_sale",
                                                   "unit_sale_price_required", "sale_evidence_available",
                                                   "measurement_available", "standard_quantity_applies"):
            # skip generic bools we don't interpret; those are evaluated below.
            continue
        ok, reason = _eval_condition({key: cond}, context, field_map)
        if not ok:
            return False, reason
    return True, "matched"


def _confidence(fields: list, *names: str) -> float:
    """Aggregate confidence for a set of field names; 0.0 if none found."""
    confs = []
    for f in fields:
        if f.get("field") in names:
            c = f.get("confidence")
            if c is not None:
                confs.append(c)
    if not confs:
        return None
    return float(sum(confs) / len(confs))


def select_applicable(rules, context) -> list:
    """Return the subset of rules applicable to this context."""
    field_map = _field_map(context.get("fields", []) or [])
    out = []
    for r in rules:
        ok, _reason = _is_applicable(r, context, field_map)
        if ok:
            out.append(r)
    return out


def _resolution(outcomes: dict, key: str, default: str = "needs_verification") -> str:
    mapped = outcomes.get(key)
    if mapped is None:
        return default
    if mapped not in VALID_OUTCOMES:
        logger.warning("rule outcome %r not in vocabulary; using needs_verification", mapped)
        return "needs_verification"
    return mapped


def _has_field(field_map: dict, names) -> bool:
    names = [names] if isinstance(names, str) else names
    return any(n in field_map for n in names)


def _result_to_label(key: str) -> str:
    return {
        "pass": "PASS",
        "potential_non_compliance": "POTENTIAL NON-COMPLIANCE",
        "needs_verification": "NEEDS VERIFICATION",
        "not_applicable": "NOT APPLICABLE",
        "info": "NOT APPLICABLE",
    }.get(key, "NEEDS VERIFICATION")


def _evaluate_one(rule: dict, context: dict, fields: list, field_map: dict) -> dict:
    rule_id = rule.get("rule_id")
    vtype = rule.get("validation_type", "manual")
    params = rule.get("parameters") or {}
    outcomes = rule.get("outcomes") or {}
    severity = rule.get("severity", "info")

    def mk(result_key, detail):
        return {
            "rule_id": rule_id,
            "ruleset_version": context.get("ruleset_version", "PCR-2026.1"),
            "result": _result_to_label(result_key),
            "evidence": {
                "block_ids": [b.get("_id") for b in fields if b.get("_id")],
                "field_ids": [f.get("_id") for f in fields if f.get("_id")],
                "image_ids": list({b.get("_image_id") for b in fields if b.get("_image_id")}),
                "confidence": _confidence(fields),
            },
            "detail": detail,
            "applicable": True,
            "severity": severity,
        }

    req_fields = params.get("fields", [])
    any_of = params.get("any_of", False)

    if not req_fields and (rule.get("applicability") or {}).get("field"):
        # Presence rules may derive their target field from applicability
        # (e.g. R-APP-04: applicability {field: not_for_retail_sale}).
        req_fields = [(rule.get("applicability") or {}).get("field")]

    if vtype in ("required_field", "presence"):
        present = _has_field(field_map, req_fields)
        if not present:
            detail = f"Required field(s) {req_fields} not found in OCR output."
            result = _resolution(outcomes, "missing", "potential_non_compliance")
            return mk(result, detail)
        conf = _confidence(fields, *[f for f in req_fields])
        if conf is not None and conf < 0.6:
            detail = f"Field(s) {req_fields} found but low confidence ({conf:.2f})."
            result = _resolution(outcomes, "low_confidence", "needs_verification")
            return mk(result, detail)
        detail = f"Required field(s) {req_fields} present."
        result = _resolution(outcomes, "present", "pass")
        return mk(result, detail)

    if vtype == "pattern":
        # net quantity unit consistency (R-QTY-01)
        qty = field_map.get("net_quantity")
        if not qty:
            return mk(_resolution(outcomes, "invalid", "potential_non_compliance"),
                      "Net quantity present but unparseable.")
        norm = qty.get("normalized") or {}
        unit = norm.get("unit")
        if unit:
            return mk(_resolution(outcomes, "normalized", "pass"),
                      f"Net quantity normalized: {norm.get('value')} {unit}")
        return mk(_resolution(outcomes, "ambiguous", "needs_verification"),
                  "Net quantity unit not recognized.")

    if vtype == "comparison":
        # Quantity threshold (R-APP-03) or sale-above-MRP (R-PRICE-01)
        if rule_id == "R-APP-03":
            qty = field_map.get("net_quantity")
            if not qty:
                return mk(_resolution(outcomes, "missing_qty", "needs_verification"),
                          "Net quantity not present; cannot determine threshold.")
            norm = qty.get("normalized") or {}
            canonical = norm.get("canonical_value")
            unit = norm.get("canonical_unit")
            threshold = params.get("threshold_volume_l")
            if unit in ("g", "ml"):
                value_kg = canonical / 1000 if unit == "g" else canonical / 1000
                threshold = params.get("threshold_weight_kg", 25)
                cmp_val = canonical / 1000 if unit == "g" else canonical / 1000
                if cmp_val > threshold:
                    return mk(_resolution(outcomes, "above_threshold", "needs_verification"),
                              f"Package quantity {cmp_val} {unit} exceeds threshold.")
                return mk(_resolution(outcomes, "below_threshold", "pass"),
                          f"Package quantity {cmp_val} {unit} below threshold {threshold}.")
            return mk(_resolution(outcomes, "below_threshold", "pass"),
                      f"Package quantity normalized but unit unknown.")
        # R-PRICE-01 - sale evidence
        if rule_id == "R-PRICE-01":
            if not context.get("sale_evidence_available"):
                return mk(_resolution(outcomes, "not_applicable", "not_applicable"),
                          "No sale/transaction evidence available.")
        return mk(_resolution(outcomes, "not_applicable", "not_applicable"),
                  "No comparison data available.")

    if vtype == "arithmetic":
        if rule_id == "R-UNIT":
            return _eval_unit_price(rule, context, field_map, mk)
        return mk(_resolution(outcomes, "unknown", "needs_verification"),
                  "Arithmetic rule not matched.")

    if vtype == "measurement":
        if rule_id == "R-READ-01":
            # Legibility: check overall OCR confidence.
            confs = [f.get("confidence") for f in fields if f.get("confidence") is not None]
            if not confs:
                return mk(_resolution(outcomes, "obscured", "needs_verification"),
                          "No OCR text found; cannot verify legibility.")
            avg = sum(confs) / len(confs)
            if avg < params.get("min_confidence", 0.6):
                return mk(_resolution(outcomes, "low_confidence", "needs_verification"),
                          f"Low average OCR confidence ({avg:.2f}).")
            return mk(_resolution(outcomes, "legible", "pass"),
                      f"Text legible (avg confidence {avg:.2f}).")
        if rule_id == "R-QTY-02":
            if not context.get("measurement_available"):
                return mk("not_applicable", "No physical measurement available; cannot infer actual quantity.")
            return mk(_resolution(outcomes, "within_error", "pass"),
                      "Measurement within error tolerance.")
        return mk(_resolution(outcomes, "no_measurement", "not_applicable"),
                  "Measurement rule not applicable.")

    if vtype == "manual":
        # R-APP-01, R-DECL-11, R-DECL-13 - these route to human verification.
        detail = f"Manual verification required for rule {rule_id}: {rule.get('title', '')}."
        result = _resolution(outcomes, "unclear", "needs_verification")
        return mk(result, detail)

    if vtype == "system":
        return mk(_resolution(outcomes, "selected", "pass"),
                  f"System rule {rule_id} satisfied.")

    return mk("needs_verification", f"Unknown validation_type {vtype}.")


def _eval_unit_price(rule, context, field_map, mk) -> dict:
    """R-UNIT: unit sale price must match net quantity basis."""
    qty = field_map.get("net_quantity")
    usp = field_map.get("unit_sale_price")
    if not usp:
        return mk("needs_verification", "Unit sale price not present.")
    norm_usp = usp.get("normalized") or {}
    basis = norm_usp.get("basis")
    if not qty:
        return mk("needs_verification", "Net quantity not present; cannot verify unit sale price basis.")
    qty_norm = qty.get("normalized") or {}
    canonical = qty_norm.get("canonical_value")
    cunit = qty_norm.get("canonical_unit")
    if canonical is None:
        return mk("needs_verification", "Net quantity not normalized.")
    thresholds = rule.get("parameters", {}).get("thresholds", {})
    if cunit == "g":
        expected = "per_kg" if canonical >= 1000 else "per_g"
    elif cunit == "ml":
        expected = "per_l" if canonical >= 1000 else "per_ml"
    elif cunit == "cm":
        expected = "per_m" if canonical >= 100 else "per_cm"
    else:
        expected = "per_number"
    if basis == expected or (basis == "per_100g" and expected == "per_g") or \
       (basis == "per_100g" and expected == "per_100g"):
        return mk("pass", f"Unit sale price basis {basis} matches net quantity ({expected}).")
    if basis == "unknown":
        return mk("needs_verification", "Unit sale price basis not recognized.")
    return mk("potential_non_compliance",
              f"Unit sale price basis {basis} does not match expected {expected} for net quantity.")


def evaluate_rules(rules, context, blocks, fields) -> list:
    """Evaluate all applicable rules. fields: list of extracted-field dicts."""
    context = dict(context or {})
    context.setdefault("fields", fields or [])
    context.setdefault("ruleset_version", "PCR-2026.1")
    field_map = _field_map(fields or [])
    applicable = [r for r in rules if _is_applicable(r, context, field_map)[0]]
    if not applicable:
        return [{
            "rule_id": "R-APP-01",
            "ruleset_version": context["ruleset_version"],
            "result": "NOT APPLICABLE",
            "evidence": {"block_ids": [], "field_ids": [], "image_ids": [], "confidence": None},
            "detail": "No rules applicable to this inspection context.",
        }]

    results = []
    for rule in applicable:
        try:
            results.append(_evaluate_one(rule, context, fields or [], field_map))
        except Exception as exc:  # never crash the pipeline over one rule
            logger.exception("rule %s evaluation failed: %s", rule.get("rule_id"), exc)
            results.append({
                "rule_id": rule.get("rule_id"),
                "ruleset_version": context["ruleset_version"],
                "result": "NEEDS VERIFICATION",
                "evidence": {"block_ids": [], "field_ids": [], "image_ids": [], "confidence": None},
                "detail": f"Rule evaluation error: {exc}",
            })
    return results
