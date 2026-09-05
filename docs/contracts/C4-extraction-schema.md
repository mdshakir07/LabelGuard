# Contract C-4 — Extraction Schema

Owner: **B (CV/OCR + Rules)**. Consumers: A (storage/API), C (assessment table). PRD §12. Never silently overwrite low-confidence raw text (PRD §24).

## Field list (PRD §12)
`product_name`, `manufacturer_name`, `manufacturer_address`, `packer_name`, `packer_address`, `importer_name`, `importer_address`, `country_of_origin`, `net_quantity`, `net_unit`, `mrp`, `mrp_tax_inclusive`, `unit_sale_price`, `manufacture_month`, `manufacture_year`, `best_before`, `consumer_contact_name`, `consumer_phone`, `consumer_email`, `dimensions`, `barcode_gtin_qr`, `gm_marking`, `veg_nonveg_marking`, `not_for_retail_sale`.

## Extracted field record (API + DB `extracted_fields`)
```json
{
  "id": 41,
  "field_name": "mrp",
  "raw_value": "Rs. 129.75",
  "normalized_value": {"amount": 129.75, "currency": "INR", "tax_inclusive": false, "basis": "label"},
  "confidence": 0.94,
  "source_ocr_ids": [12],
  "is_edited": false
}
```

## Normalized value shapes (key fields)
- **mrp** → `{"amount": float, "currency": "INR", "tax_inclusive": bool|null, "rounding_paise": int|null}` (PRD §14)
- **net_quantity / net_unit** → `{"value": float, "unit": "g|kg|ml|l|cm|m|nos|pcs|pairs|sets", "canonical_unit": "g|ml|...", "canonical_value": float}` (PRD §15; kg↔g, L↔ml conversions)
- **unit_sale_price** → `{"price": float, "currency": "INR", "basis": "per_g|per_kg|per_cm|per_m|per_number|per_ml|per_l|unknown"}` (PRD §13 table)
- **manufacture_month/manufacture_year** → `{"month": 1-12, "year": int}`
- **best_before** → `{"kind": "best_before|use_by|expiry", "date": "2027-05-31"|null, "months": 12|null}`
- **consumer_phone** → `{"phone": "+91xxxxxxxxxx"}`
- **consumer_email** → `{"email": "..."}`
- **country_of_origin** → `{"country": "China"}` (country dictionary normalized)
- **barcode_gtin_qr** → `{"present": bool, "kind": "barcode|gtin|qr|none", "value": "..."}`

## Rules
- `raw_value` is always preserved; `normalized_value` may be null if unparseable but confidence is retained for a `needs_verification` route.
- `is_edited=true` when an inspector corrected the value; original raw_value untouched; audit logged.
- Extraction confidence drives R-READ-01, which downgrades low-confidence fields to `NEEDS VERIFICATION`.