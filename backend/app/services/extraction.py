"""B-OWNED service: field extraction + normalization (replaces placeholder).

Parses raw OCR blocks into C-4 fields with normalized values. Raw OCR is
always preserved; normalized_value may be null if unparseable. Confidence is
retained for the NEEDS VERIFICATION route (R-READ-01).

Contract: blocks -> list[{"field", "raw", "normalized", "confidence",
                          "source_ocr_ids", "source_bbox"}]
"""
import re

# ---- Hints used to locate the label/field in OCR text ----------------------
_HINTS = {
    "product_name": ("product", "flavour", "variant", "brand"),
    "manufacturer_name": ("mfd. by", "made by", "manufactured by", "mfr", "by m/s"),
    "manufacturer_address": ("mfd by:", "mfg by:", "regd. office", "registered office"),
    "packer_name": ("packed by", "packer", "packaged by"),
    "packer_address": ("packed at", "packing at"),
    "importer_name": ("imported by", "importer"),
    "importer_address": ("imported at", "importer address"),
    "country_of_origin": ("made in", "product of", "country of origin", "origin"),
    "net_quantity": ("net wt", "net weight", "net qty", "net quantity", "net content", "weight", "net "),
    "mrp": ("mrp", "m.r.p", "maximum retail price", "retail price", "r.s", "rs.", "rs ", "price incl", "incl. of all taxes"),
    "unit_sale_price": ("per unit", "per kg", "per 100", "per piece", "price per", "unit price", "per 10", "per gm", "per g"),
    "manufacture_month": ("mfg date", "mfg.", "mfd date", "manufacture date", "date of manufacture", "manufacturing date", "mfg"),
    "best_before": ("best before", "use by", "expiry", "exp date", "exp. date", "expiration", "best by"),
    "consumer_contact_name": ("customer care", "consumer care", "consumer", "helpline", "toll free", "toll-free"),
    "consumer_phone": ("tel", "phone", "contact no", "telephone", "call us",
                       "toll-free", "toll free", "helpline"),
    "consumer_email": ("e-mail", "email", "mail us"),
    "not_for_retail_sale": ("not for retail sale", "not for retail", "not for resale"),
    "veg_nonveg_marking": ("vegetarian", "non-vegetarian", "veg", "non veg", "vegetarian symbol"),
    "gm_marking": ("gm food", "genetically modified", "gm"),
    "barcode_gtin_qr": ("ean", "gtin", "upc", "barcode", "scannable", "qr"),
    "dimensions": ("dimension", "size", "mm x", "cm x", "l x b x h"),
}

# Units recognized for net quantity + canonical conversion to base unit.
_UNIT_INFO = {
    "g": {"canonical": "g", "to_base": 1.0},
    "gm": {"canonical": "g", "to_base": 1.0},
    "gram": {"canonical": "g", "to_base": 1.0},
    "grams": {"canonical": "g", "to_base": 1.0},
    "gr": {"canonical": "g", "to_base": 1.0},
    "kg": {"canonical": "g", "to_base": 1000.0},
    "kilogram": {"canonical": "g", "to_base": 1000.0},
    "kilograms": {"canonical": "g", "to_base": 1000.0},
    "ml": {"canonical": "ml", "to_base": 1.0},
    "milliliter": {"canonical": "ml", "to_base": 1.0},
    "millilitre": {"canonical": "ml", "to_base": 1.0},
    "l": {"canonical": "ml", "to_base": 1000.0},
    "lt": {"canonical": "ml", "to_base": 1000.0},
    "litre": {"canonical": "ml", "to_base": 1000.0},
    "litres": {"canonical": "ml", "to_base": 1000.0},
    "liter": {"canonical": "ml", "to_base": 1000.0},
    "cm": {"canonical": "cm", "to_base": 1.0},
    "centimeter": {"canonical": "cm", "to_base": 1.0},
    "m": {"canonical": "cm", "to_base": 100.0},
    "metre": {"canonical": "cm", "to_base": 100.0},
    "meter": {"canonical": "cm", "to_base": 100.0},
}

_NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?")
_CURRENCY_RE = re.compile(r"(rs\.?|inr|rupees?|\u20b9)", re.IGNORECASE)
_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _all_numbers(text: str) -> list:
    return [float(n.replace(",", "")) for n in _NUMBER_RE.findall(text)]


def _find_unit(text: str):
    """Return (unit_key, canonical_unit, to_base) if a unit appears in text."""
    low = text.lower()
    for unit, info in _UNIT_INFO.items():
        if re.search(r"\b" + re.escape(unit) + r"\b", low):
            return unit, info["canonical"], info["to_base"]
    return None, None, None


def _normalize_qty(text: str):
    nums = _all_numbers(text)
    if not nums:
        return None
    unit, canonical, to_base = _find_unit(text)
    value = nums[0]
    data = {"value": value, "unit": unit}
    if unit:
        data["canonical_unit"] = canonical
        data["canonical_value"] = round(value * to_base, 4)
    return data


def _normalize_mrp(text: str):
    nums = [n for n in _all_numbers(text) if n >= 0]
    if not nums:
        return None
    # Heuristic: pick the largest value (MRP label on Indian packages).
    amount = max(nums)
    currency = "INR" if _CURRENCY_RE.search(text) else None
    tax_inclusive = bool(re.search(r"incl\.?\s*(?:of)?\s*all\s*taxes|inclusive", text, re.IGNORECASE))
    # Rounding to nearest 5 paise if a whole-paise MRP.
    paise = round((amount * 100) % 100)
    rounding = None
    if paise % 5 != 0 and paise > 0:
        rounding = paise
    return {"amount": amount, "currency": currency, "tax_inclusive": tax_inclusive,
            "rounding_paise": rounding}


def _normalize_unit_price(text: str):
    nums = [n for n in _all_numbers(text) if n >= 0]
    if not nums:
        return None
    price = min(nums)
    low = text.lower()
    basis = "unknown"
    if any(k in low for k in ("per kg", "per kilo")):
        basis = "per_kg"
    elif any(k in low for k in ("per g", "per gm", "per gram")):
        basis = "per_g"
    elif "per 100" in low:
        basis = "per_100g"
    elif any(k in low for k in ("per l", "per litre", "per liter")):
        basis = "per_l"
    elif any(k in low for k in ("per ml", "per millilit")):
        basis = "per_ml"
    elif any(k in low for k in ("per m", "per meter", "per metre")):
        basis = "per_m"
    elif any(k in low for k in ("per cm", "per centi")):
        basis = "per_cm"
    elif any(k in low for k in ("per piece", "per unit", "per number", "each")):
        basis = "per_number"
    return {"price": price, "currency": "INR", "basis": basis}


def _normalize_date(text: str):
    low = text.lower()
    month = None
    year = None
    # Month name
    for name, num in _MONTHS.items():
        if re.search(r"\b" + name + r"\w*\.?", low[:50]):
            month = num
            break
    # Numeric MM/YYYY or MMM YYYY or DD/MM/YYYY
    nums = _all_numbers(text)
    if not nums:
        return None
    if month is None and nums:
        # First number could be month if in format MM/YYYY
        m = re.search(r"(\d{1,2})[/\-](\d{4})", text)
        if m and 1 <= int(m.group(1)) <= 12:
            month = int(m.group(1))
            year = int(m.group(2))
    if year is None:
        for n in nums:
            if 1990 <= n <= 2100:
                year = int(n)
                break
    if month is None and len(nums) >= 2:
        # DD/MM/YYYY -> 2nd number
        m = re.search(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", text)
        if m and 1 <= int(m.group(2)) <= 12:
            month = int(m.group(2))
            year = int(m.group(3))
    if month is None and year is None:
        return None
    return {
        "month": month if 1 <= month <= 12 else None,
        "year": year if year is not None else None,
    }
    if not nums:
        return None
    return {"month": month, "year": year}


def _normalize_phone(text: str):
    m = re.search(r"(?:\+?\d{1,3}[\s-]?)?(?:\d{5}[\s-]?\d{5}|\d{10})", text)
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) == 10:
        return {"phone": "+91" + digits}
    if len(digits) == 12 and digits.startswith("91"):
        return {"phone": "+" + digits}
    if len(digits) == 11 and digits.startswith("0"):
        return {"phone": "+91" + digits[1:]}
    if m:
        return {"phone": m.group(0).strip()}
    return None


def _normalize_email(text: str):
    m = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
    if m:
        return {"email": m.group(0)}
    return None


def _normalize_country(text: str):
    low = text.lower()
    for country in ("india", "china", "usa", "united states", "japan", "korea",
                    "uae", "bangladesh", "nepal", "taiwan", "germany", "thailand",
                    "vietnam", "indonesia", "malaysia", "singapore", "uk", "italy",
                    "france", "canada", "australia", "sri lanka", "pakistan"):
        if country in low:
            return {"country": country.title()}
    # "made in" -> following word
    m = re.search(r"made\s+in\s+([A-Za-z]+)", text, re.IGNORECASE)
    if m:
        return {"country": m.group(1).title()}
    return None


def _normalize_barcode(text: str):
    low = text.lower().strip()
    if any(k in low for k in ("qr", "barcode", "ean", "gtin")):
        digits = "".join(ch for ch in text if ch.isdigit())
        return {"present": True, "kind": "barcode" if "qr" not in low else "qr", "value": digits or None}
    return None


def _normalize_contact_name(text: str):
    clean = re.sub(r"(customer|customers?\s*(?:care|service)|helpline|toll[- ]?free|call\s*us)\s*[:.\-]*",
                   "", text, flags=re.IGNORECASE).strip(": .-")
    clean = re.sub(r"[\-:].*$", "", clean).strip()
    return {"name": clean} if clean else None


_NORMALIZERS = {
    "net_quantity": _normalize_qty,
    "mrp": _normalize_mrp,
    "unit_sale_price": _normalize_unit_price,
    "manufacture_month": _normalize_date,
    "best_before": _normalize_date,
    "consumer_phone": _normalize_phone,
    "consumer_email": _normalize_email,
    "country_of_origin": _normalize_country,
    "barcode_gtin_qr": _normalize_barcode,
    "consumer_contact_name": _normalize_contact_name,
}


def _score_block(block: dict, hints: tuple) -> float:
    """Heuristic: how strongly a block's text looks like the target field.

    Returns 0 if no hint matches. A small bonus is added when the text also
    carries digits, but only after at least one hint has matched.
    """
    text = (block.get("text") or "").lower()
    score = 0.0
    for hint in hints:
        if hint and hint in text:
            score += 1.0
    if score == 0:
        return 0.0
    # Prefer blocks that carry digits for numeric fields.
    if _NUMBER_RE.search(text):
        score += 0.3
    return score


def extract_fields(blocks: list) -> list:
    """Select best-scoring OCR block per field and produce a normalized value."""
    fields = []
    for field_name, hints in _HINTS.items():
        candidates = [b for b in blocks if _score_block(b, hints) > 0]
        if not candidates:
            continue
        best = max(candidates, key=lambda b: (_score_block(b, hints), b.get("confidence") or 0))
        raw = best["text"]
        norm = None
        if field_name in _NORMALIZERS:
            try:
                norm = _NORMALIZERS[field_name](raw)
            except Exception:
                norm = None
        fields.append({
            "field": field_name,
            "raw": raw,
            "normalized": norm,
            "confidence": best.get("confidence"),
            "source_ocr_ids": [best.get("_id")] if best.get("_id") else [],
            "source_bbox": best.get("bbox"),
        })
    return fields
