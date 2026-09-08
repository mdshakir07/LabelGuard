"""B-OWNED service: commodity-category suggestion for the confirmation step
(PRD §18, §40 P0).

After extraction, the inspector confirms the commodity category before
applicability rules run. This service suggests categories deterministically
from inspection metadata + extracted product hints. It never decides — the
inspector confirms or overrides (the human gate).
"""
import re

# Keyword -> category scores. Prefer specific terms that appear early.
_CATEGORY_KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "food": [
        ("biscuit", 5), ("chips", 5), ("chocolate", 5), ("cereal", 4),
        ("rice", 4), ("atta", 4), ("flour", 4), ("sugar", 4), ("salt", 4),
        ("spice", 4), ("masala", 4), ("noodle", 4), ("soup", 4), ("juice", 3),
        ("milk", 4), ("cheese", 4), ("butter", 4), ("oil", 3), ("ghee", 4),
        ("ready to eat", 4), ("snack", 4), ("namkeen", 4), ("candy", 4),
        ("jelly", 4), ("jam", 4), ("paneer", 4), ("tea", 3), ("coffee", 3),
        ("pickle", 4), ("chutney", 4), ("papad", 4), ("dahi", 4), ("pasta", 4),
        ("sauce", 4), ("ketchup", 4), ("soup", 3), ("beverage mix", 3),
        ("dry fruit", 4), ("honey", 4), ("peanut butter", 5), ("vermicelli", 4),
    ],
    "beverages": [
        ("soft drink", 5), ("cola", 5), ("soda", 4), ("energy drink", 5),
        ("sports drink", 5), ("water", 3), ("beer", 5), ("wine", 5),
        ("whisky", 5), ("rum", 5), ("vodka", 5), ("liquor", 5), ("liqueur", 5),
        ("carbonated", 4), ("squash", 4), ("syrup", 3), ("malt", 3),
        ("kombucha", 5), ("iced tea", 4), ("fruit drink", 4), ("tonic", 3),
    ],
    "cosmetics": [
        ("shampoo", 5), ("soap", 4), ("cream", 4), ("lotion", 4), ("lotion", 4),
        ("hair oil", 5), ("toothpaste", 5), ("deodorant", 5), ("perfume", 5),
        ("surfactant", 4), ("face wash", 5), ("sunscreen", 5), ("lip balm", 5),
        ("makeup", 4), ("lipstick", 5), ("nail polish", 5), ("body wash", 5),
        ("conditioner", 5), ("powder", 3), ("talc", 4), ("serum", 4),
        ("veneshave", 4), ("aftershave", 5), ("dry shampoo", 5),
    ],
    "garments": [
        ("t-shirt", 5), ("tshirt", 5), ("shirt", 4), ("dress", 4), ("jeans", 5),
        ("trouser", 4), ("kurta", 5), ("saree", 5), ("sari", 5), ("fabric", 3),
        ("garment", 4), ("hosiery", 4), ("woolen", 4), ("socks", 5),
        ("innerwear", 4), ("sweater", 5), ("jacket", 4), ("track suit", 5),
        ("nightwear", 4), ("lingerie", 5), ("towel", 3), ("handloom", 4),
    ],
    "household": [
        ("detergent", 5), ("soap bar", 4), ("dishwash", 5), ("cleaner", 4),
        ("bleach", 5), ("disinfectant", 5), ("toilet cleaner", 5),
        ("candle", 3), ("match", 3), ("air freshener", 5), ("insecticide", 4),
        ("repellent", 4), ("battery", 4), ("bulb", 4), ("lamp", 3),
        ("brush", 3), ("sponge", 3), ("bucket", 3), ("bag", 2),
        ("storage box", 4), ("cling wrap", 4), ("aluminium foil", 4),
        ("kitchen towel", 4), ("garbage bag", 5),
    ],
    "agricultural_produce": [
        ("potato", 5), ("onion", 5), ("tomato", 5), ("apple", 4), ("banana", 4),
        ("mango", 4), ("grape", 4), ("carrot", 5), ("garlic", 5), ("ginger", 5),
        ("green chilli", 5), ("spinach", 5), ("cabbage", 5), ("cauliflower", 5),
        ("wheat", 5), ("maize", 5), ("pulses", 5), ("lentil", 5), ("dal", 5),
    ],
    "medical_device": [
        ("bandage", 5), ("syringe", 5), ("gloves", 4), ("mask", 3),
        ("thermometer", 5), ("bp monitor", 5), ("glucometer", 5),
        ("condom", 5), ("sanitary pad", 5), ("diaper", 5), ("stethoscope", 5),
    ],
    "glass_containers": [
        ("jar", 5), ("bottle", 2), ("pet", 2), ("hdp", 2),
    ],
}

# Special statuses map directly to a category.
_SPECIAL_STATUS_MAP = {
    "gm food": "food", "gm": "food",
    "garment": "garments", "hosiery": "garments",
    "medical device": "medical_device",
    "glass container": "glass_containers",
}


def suggest_categories(
    product_name_hint: str | None = None,
    special_status: str | None = None,
    extracted_product: str | None = None,
    category: str | None = None,
) -> list[dict]:
    """Deterministic keyword-based suggestions.

    Returns a list sorted by confidence (highest first) of
    ``{"category", "confidence", "basis"}``. Empty results mean no signal yet —
    the caller should recommend SKU-level confirmation by the inspector.
    """
    scores: dict[str, list[tuple[int, str]]] = {}
    texts: list[str] = []
    if extracted_product:
        texts.append(extracted_product)
    if product_name_hint:
        texts.append(product_name_hint)
    if special_status:
        key = special_status.strip().lower()
        mapped = _SPECIAL_STATUS_MAP.get(key)
        if mapped:
            scores.setdefault(mapped, []).append((8, f"special status '{special_status}'"))

    for text in texts:
        lower = text.lower()
        for cat, terms in _CATEGORY_KEYWORDS.items():
            for term, weight in terms:
                # optional trailing 's'/'es' covers common plurals (biscuit(s), jar(s))
                if re.search(rf"\b{re.escape(term)}(?:s|es)?\b", lower):
                    scores.setdefault(cat, []).append((weight, f"term '{term}' in '{text[:40]}'"))

    ranked = [
        {"category": cat, "confidence": sum(w for w, _ in entries), "basis": "; ".join(b for _, b in entries[:2])}
        for cat, entries in scores.items()
    ]
    ranked.sort(key=lambda r: r["confidence"], reverse=True)

    # Normalize to 0..1 relative to the top score (soft estimate, not a legal gate).
    if ranked:
        top = ranked[0]["confidence"]
        for r in ranked:
            r["confidence"] = round(r["confidence"] / top, 2)

    # Prefer keeping the current category visible at a fixed rank when it scored.
    if category and not any(r["category"] == category for r in ranked):
        ranked.append({"category": category, "confidence": 0.1, "basis": "current value kept"})

    return ranked[:5]