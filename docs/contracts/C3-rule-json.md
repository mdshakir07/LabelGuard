# Contract C-3 — Rule JSON v1

Owner: **B (CV/OCR + Rules)**. Consumers: A (loads + serves), C (renders), rules engine (B). PRD §19–20. Seed: `rules/versions/seed_rules_v1.json`.

## Ruleset envelope
```json
{
  "ruleset": {
    "version": "PCR-2026.1",
    "label": "...", "base_notification": "...",
    "review_status": "draft|test|published|retired",
    "effective_from": "2026-09-04", "effective_to": null,
    "source_documents": ["https://..."]
  },
  "rules": [ ... rule objects ... ]
}
```

## Rule object (PRD §19)
| key | type | notes |
|---|---|---|
| rule_id | string | Stable ID (`R-DECL-05`) |
| rule_number | string | Legal rule/sub-rule (e.g. `6(1)(c)`) |
| module | string | R-APP, R-DECL, R-PRICE, R-UNIT, R-QTY, R-DATE, R-CONTACT, R-PLACE, R-READ, R-SPECIAL, R-ECOM, R-VERSION |
| title | string | Human-readable |
| description | string | Validation statement |
| applicability | object | Structured conditions (PRD §18) evaluated BEFORE the check |
| validation_type | enum | `presence|pattern|arithmetic|measurement|comparison|manual|system|required_field` |
| parameters | object | Thresholds, unit dicts, field lists, patterns |
| severity | enum | `info|low|medium|high|critical` |
| outcomes | object | map condition → one of `pass|potential_non_compliance|needs_verification|not_applicable|info` |
| effective_from / effective_to | date | R-VERSION-01 selection |
| source_document / source_locator | string | traceability (R-VERSION-02) |
| version | string | ruleset version |

## Applicability inputs (PRD §18) evaluated by engine (B5)
`inspection_date`, `category`, `package_quantity` (`net_quantity`+`net_unit`), `channel`, `origin`, `package_structure`, `special_status`, `other_law_control`, `evidence_quality`.

## Rules of engagement
- Rules are CONDITIONAL, not forced. No rule may output more than the four automated outcomes (C-5).
- Exemptions are explicit applicability entries, never hidden in code.
- A published ruleset is immutable (PRD §37): amendments create a NEW version file (`rules/versions/seed_rules_v2.json`); old inspections keep the version snapshot in `assessments.ruleset_version`.
- B alone edits rule JSON. A only loads/serves it.