# Contract C-1 — API Specification

Owner: **A (Backend & DB)**. Consumers: C (UI), B (result writers). Locked at Phase 0 (PRD §28).

## Conventions
- Base URL: `http://localhost:8000` (dev). All JSON. Dates ISO-8601 (`YYYY-MM-DD` / RFC3339).
- Auth: `Authorization: Bearer <jwt>` for all endpoints except `/auth/login` and `/health`.
- Errors: `{"detail": "..."}` with standard HTTP status codes (422 validation, 401 unauth, 403 forbidden, 404 missing).
- IDs are integer PKs from the DB unless a UUID is noted.

## Endpoints (PRD §28 mapping)

### POST /auth/login
Body: `{"email": "...", "password": "..."}`
200 → `{"access_token": "...", "token_type": "bearer", "user": {"id": 1, "name": "...", "role": "inspector", "email": "..."}}`

### POST /inspections
Body: `{"location": "...", "channel": "retail|ecommerce|institutional|industrial", "inspection_date": "2026-09-04", "category": "...", "package_structure": "single|multi_product|multi_unit|promotional", "origin": "domestic|imported", "product_name_hint": "..."}`
201 → full inspection object (below).

Inspection object:
```json
{
  "id": 1, "inspection_id": "MM-2026-0001",
  "inspector_id": 1, "location": "...", "channel": "retail",
  "inspection_date": "2026-09-04", "category": "food",
  "status": "draft|processing|ready_for_review|reviewed|closed",
  "ruleset_version": "PCR-2026.1",
  "created_at": "2026-09-04T10:00:00Z"
}
```

### POST /inspections/{id}/images
Multipart form, field name `files`, one-or-more image files (`image/jpeg|png|webp`, ≤20 MB each). Optional form fields: `type` (front|back|side|top|bottom|closeup|listing).
201 → `{"created": [image objects], "warnings": ["blur detected — consider retake"]}`
Image object: `{"id": 3, "type": "front", "original_url": "...", "processed_url": null, "sha256": "...", "width": 3000, "height": 2000}`

### POST /inspections/{id}/process
Runs quality → preprocess → OCR → extraction → applicability → rules (owned by B). 
Accepted: `{"run_quality": true}`. 202 → `{"status": "processing"}`; client polls GET `/inspections/{id}` until `status` is `ready_for_review`.

### GET /inspections/{id}
200 → inspection object + `images`, `fields`, `assessments`, `findings` summaries (see C-4/C-5 for shapes).

### GET /inspections/{id}/fields
200 → array of extracted fields (C-4 shape).

### POST /inspections/{id}/assess
Allow re-assess (e.g., after inspector corrects a field). Body `{}`. 202 → `{"status": "processing"}`.

### PATCH /findings/{id}
Body: `{"status": "CONFIRMED|REJECTED|MANUAL VERIFICATION", "reviewer_comment": "...", "corrected_value": "..."}`
200 → updated finding with reviewer id + timestamp. Audit logged.

### POST /inspections/{id}/report
Body: `{"format": "pdf|docx"}`. 200 → `{"pdf_url": "...", "editable_url": "..."}` (generated via C6 service).

### GET /inspections?status=&category=&channel=&q=
Search/filter history (S10). 200 → `{"items": [...], "total": 12}`.

### GET /dashboard
200 → KPIs per PRD §32: totals, pass/potential/needs counts, confirmed findings, top categories, avg processing time, trends.

### GET /rules
200 → `{"ruleset_version": "...", "rules": [...]}` (C-3 shape).

### POST /rules, POST /rules/{id}/publish
Admin-only. Create rule version / publish immutable ruleset (PRD §37, FR-18).

## Deps / timing
- Findings PATCH (A5) gates C5 (review UI). Assessment GET (A5) gates C4.
- Process orchestration (A4) must call B service modules synchronously in-test; async in prod via BackgroundTasks.