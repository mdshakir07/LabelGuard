# Contract C-2 — Database Schema

Owner: **A (Backend & DB)**. Consumers: B (writes OCR/fields/assessments), C (reads via API). PRD §27. Managed with SQLAlchemy 2 + alembic.

## Tables (PRD §27 mapping)

### users
id · name · role (`inspector|reviewer|admin|auditor`) · email (unique) · password_hash · status (`active|disabled`) · created_at

### inspections
id · public_id (`MM-YYYY-NNNN` unique) · inspector_id → users · location · channel (`retail|ecommerce|institutional|industrial`) · inspection_date · category · package_structure (`single|multi_product|multi_unit|promotional`) · origin (`domestic|imported`) · special_status (`gm_food|garment|medical_device|...`) · status (`draft|processing|ready_for_review|reviewed|closed`) · ruleset_version · created_at · closed_at

### products
id · name · brand · category · manufacturer · origin · first_seen_at · (product-level history key)

### inspection_images
id · inspection_id → inspections · type (`front|back|side|top|bottom|closeup|listing`) · original_url · processed_url · sha256 · width · height · quality_score_json · created_at

### ocr_blocks
id · image_id → inspection_images · text · confidence · x · y · width · height · source (`original|enhanced`) · created_at

### extracted_fields
id · inspection_id → inspections · field_name (C-4 key) · raw_value · normalized_value (JSON, C-4) · confidence · source_ocr_ids (int[]) · is_edited (bool) · created_at

### rules
id · rule_id (unique, e.g. `R-DECL-05`) · rule_number · module · title · description · conditions JSON (C-3) · validation JSON · parameters JSON · severity (`info|low|medium|high|critical`) · effective_from · effective_to · source_document · source_locator · version · status (`draft|test|published|retired`) · published_at

### assessments
id · inspection_id → inspections · rule_id → rules · result (`PASS|POTENTIAL NON-COMPLIANCE|NEEDS VERIFICATION|NOT APPLICABLE`) · confidence · explanation · created_at · ruleset_version (snapshot)

### findings
id · assessment_id → assessments · severity · status (`PENDING|CONFIRMED|REJECTED|MANUAL VERIFICATION`) · evidence_image_id → inspection_images · bbox JSON · ocr_block_id → ocr_blocks · extracted_field_id → extracted_fields · reviewer_id → users (nullable) · reviewer_comment · corrected_value · reviewed_at · created_at

### measurements
id · inspection_id → inspections · type (`weight|volume|dimension|character_height`) · value · unit · method (`calibrated|manual`) · device_note · evidence_id → inspection_images · created_at

### reports
id · inspection_id → inspections · pdf_url · editable_url · generated_by → users · generated_at

### audit_logs
id · actor_id → users (nullable for system) · action · entity_type · entity_id · before_json · after_json · timestamp

## Constraints & rules
- Enums stored as strings; enforced in Python (Pydantic enums) + CHECK constraints via migration.
- `assessments.result` limited to the FOUR automated outcomes only (C-5). Human state lives on `findings.status`.
- Findings may have `evidence_image_id` NULL when evidence is a measurement (see `measurements`).
- Original images immutable after inspection `closed` (PRD §34): enforce at API layer (A).
- JSON columns: `quality_score_json`, `normalized_value`, `conditions_json`, `validation_json`, `parameters_json`, `bbox`, `before_json`, `after_json` → SQLAlchemy `JSONB` on PostgreSQL.