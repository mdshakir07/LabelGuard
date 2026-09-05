# Contract C-5 — Assessment Model

Owner: **B (CV/OCR + Rules)**. Consumers: A (API storage), C (UI labels/content). PRD §21–22. THE golden-rule enforcement point.

## Outcome vocabulary — STRICT
Automated `assessments.result` is limited to EXACTLY four values (PRD §6, §21):
`PASS` | `POTENTIAL NON-COMPLIANCE` | `NEEDS VERIFICATION` | `NOT APPLICABLE`

No other strings anywhere in generated content. UI must render these verbatim. Never map to "illegal"/"violation"/"compliant" without a human `CONFIRMED`.

## State machine (PRD §21)
| Stage | state | owner |
|---|---|---|
| Automated | PASS | engine |
| Automated | POTENTIAL NON-COMPLIANCE | engine |
| Automated | NEEDS VERIFICATION | engine |
| Human | CONFIRMED / REJECTED / MANUAL VERIFICATION | reviewer (via PATCH /findings/{id}) |
| Final | CLOSED (inspection) | reviewer |

Engine creates assessments; findings carry review status. Human review NEVER overwrites the automated result — it adds a human layer alongside.

## Assessment record
```json
{
  "id": 7,
  "rule_id": "R-DECL-05",
  "rule_number": "6(1)(c)",
  "title": "Net quantity",
  "result": "POTENTIAL NON-COMPLIANCE",
  "confidence": 0.92,
  "explanation": "net_quantity not found in OCR output.",
  "ruleset_version": "PCR-2026.1",
  "applicable": true,
  "created_at": "2026-09-04T10:00:00Z"
}
```

## Finding record (evidence + review)
```json
{
  "id": 13,
  "assessment_id": 7,
  "severity": "critical",
  "status": "PENDING",
  "evidence_image_id": 3,
  "bbox": {"x": 100, "y": 220, "width": 640, "height": 40},
  "ocr_block_id": 12,
  "ocr_text": "Net wt. 500 g",
  "extracted_field_id": 41,
  "reviewer_id": null,
  "reviewer_comment": null,
  "reviewed_at": null
}
```

## Evidence-first rule (PRD §22)
Every finding MUST carry at least one of: `evidence_image_id`+`bbox`, `ocr_block_id`, or `extracted_field_id` + a `measurements` link. No evidence → finding is invalid (engine rejects it, B tests cover it).

## Enforced in code
- Rules service (B): instantiates assessments/findings; validates result vocabulary + evidence links before persist.
- API (A): DTO enums reject any out-of-vocabulary result; PATCH accepts only `CONFIRMED|REJECTED|MANUAL VERIFICATION`.
- UI (C): renders the automated result verbatim and shows review controls that add, not overwrite.