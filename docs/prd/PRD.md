# MitraMetrology AI — Complete Product Requirements Document (PRD)

SIH Problem Statement 26034 — Software System to Check Compliance of Packaged Commodities under the Legal Metrology (Packaged Commodities) Rules, 2011
Tagline: Scan. Verify. Explain. Enforce.
Version: 2.0 | Date: 04 September 2026 | Status: Hackathon Build Specification
Scope: Image/label inspection + OCR + computer vision + deterministic legal rules engine + human verification + evidence + reports + repository + dashboard + e-commerce extension

## 1. Document Control
| Item | Value |
|---|---|
| Product | MitraMetrology AI |
| Problem Statement | SIH PS 26034 |
| Authority / Domain | Department of Consumer Affairs, Ministry of Consumer Affairs, Food & Public Distribution |
| Primary legal reference | Legal Metrology (Packaged Commodities) Rules, 2011 and applicable amendments |
| Primary users | Legal Metrology inspectors/officers, enforcement teams, administrators, authorized reviewers |
| Primary input | Package photos, labels, scans, screenshots/listings |
| Primary output | Evidence-backed compliance assessment and editable/PDF report |
| Automation philosophy | AI assists extraction/vision; deterministic rule engine decides automated rule outcomes; officer confirms legal conclusion |
| Current-rule policy | Rules are versioned by effective date and source notification |

## 2. Executive Summary
MitraMetrology AI is a single inspection workflow for checking packaged commodities against applicable declaration, quantity, pricing, readability, placement and e-commerce requirements. An inspector uploads or captures package images. The system performs quality checks, image correction, computer-vision region detection and OCR, then converts OCR output into structured declarations. A versioned rules engine evaluates only the requirements applicable to the commodity, package type, channel, date and known exemptions.
Every finding is evidence-first: the result stores the rule identifier/version, source, extracted value, OCR confidence, image region, reason and reviewer status. Automated results are labelled as PASS, POTENTIAL NON-COMPLIANCE or NEEDS VERIFICATION until an authorized human reviewer confirms them. This prevents an LLM from inventing or making unsupported legal conclusions.

## 3. Problem Statement
- Manual inspection of printed declarations is slow, repetitive and difficult to standardize.
- Images may contain multiple surfaces, curved labels, glare, skew, small text and multilingual content.
- Rules have amendments and conditional applicability, so a static checklist can become legally stale.
- Inspectors need evidence showing exactly where a suspected issue was detected.
- E-commerce listings can expose inconsistent or incomplete information compared with the physical package.
- Reports should be reproducible, auditable and easy to export.

## 4. Product Vision
Turn a package inspection from a manual visual search into a traceable evidence pipeline: Capture → Quality Gate → OCR/CV → Structured Declarations → Applicability → Rule Engine → Evidence → Human Review → Report → Repository → Analytics.

## 5. Goals
- Reduce time required for first-pass package screening.
- Detect missing, inconsistent or potentially non-compliant declarations.
- Make every automated finding explainable and evidence-linked.
- Support amendment-aware, effective-date-aware rules.
- Support manual override/confirmation without losing the automated result.
- Produce PDF and editable reports.
- Maintain inspection history and product-level history.
- Provide a clean demo workflow suitable for a 5-minute SIH presentation.

## 6. Non-Goals
- The system is not a replacement for statutory enforcement authority or an officer's legal judgment.
- It does not automatically impose penalties or initiate prosecution.
- It does not claim perfect font-size measurement from arbitrary photographs.
- It does not treat a language model's answer as the legal source of truth.
- It does not assume every declaration applies to every commodity; applicability is conditional.
- It does not require live scraping of every e-commerce platform for the MVP.

## 7. Users and Roles
| Role | Permissions |
|---|---|
| Inspector | Create inspection, upload/capture evidence, review OCR, confirm category, review findings, export report |
| Reviewer/Senior Officer | Review/confirm/reject findings, request manual verification, close inspection |
| Admin | Manage users, categories, rule versions, source documents, configuration |
| Auditor/Read-only | View closed inspections, evidence, reports and audit trail |
| System | Run OCR/CV, normalize fields, execute deterministic rules, create evidence links |

## 8. End-to-End Workflow
1. Login and role authorization.
2. Create New Inspection and enter inspection metadata.
3. Select package type/channel and optionally identify commodity category.
4. Capture/upload front, back, side, top/bottom and close-up images as available.
5. Run image-quality gate; request retake if blur, glare, crop or resolution is insufficient.
6. Preprocess images: rotate, deskew, perspective correction, denoise, contrast/sharpen and crop.
7. Detect package/label/text regions using computer vision.
8. Run OCR; store text, confidence and bounding boxes.
9. Extract declaration fields from OCR spans and normalize values.
10. Detect/confirm category and package attributes.
11. Load ruleset using inspection date, commodity attributes, channel and exemptions.
12. Run deterministic checks.
13. Generate findings with evidence boxes and rule citations.
14. Route uncertain findings to human verification.
15. Inspector confirms/rejects/requests manual verification.
16. Generate PDF/editable report.
17. Save inspection, evidence, rule version and audit trail.
18. Update dashboard and product history.

## 9. Functional Requirements
| ID | Feature | Requirement |
|---|---|---|
| FR-01 | Authentication | Secure login and role-based access. |
| FR-02 | Inspection | Create unique inspection ID and metadata. |
| FR-03 | Evidence Upload | Upload multiple images per inspection; preserve originals. |
| FR-04 | Quality Gate | Score blur, glare, crop, resolution, orientation and text visibility. |
| FR-05 | Preprocessing | Create derived images without altering originals. |
| FR-06 | OCR | Extract text with confidence and bounding boxes. |
| FR-07 | Field Extraction | Map text to legal declaration fields. |
| FR-08 | Normalization | Normalize currency, quantities, units, dates, phone/email and country names. |
| FR-09 | Category | Suggest category and allow inspector confirmation/change. |
| FR-10 | Applicability | Determine applicable rules and exemptions. |
| FR-11 | Rules Engine | Run versioned deterministic validations. |
| FR-12 | Evidence | Highlight exact image regions supporting each result. |
| FR-13 | Review | Allow Confirm, Reject and Needs Manual Verification. |
| FR-14 | Reports | Generate PDF and editable report. |
| FR-15 | Repository | Search/filter historical inspections and products. |
| FR-16 | Dashboard | Show inspection and finding analytics. |
| FR-17 | Audit | Log important user/system actions. |
| FR-18 | Rule Admin | Maintain rule versions, effective dates and source references. |
| FR-19 | E-commerce | Accept listing screenshot/URL data as an extension. |
| FR-20 | Export | Export inspection package including evidence and findings. |

## 10. Legal Coverage Model
The PRD separates legal source coverage from machine-checkability. The rules below are the implementation checklist for the product. Some legal provisions are conditional, category-specific, measurement-dependent or dependent on another law. Those must be represented as conditional rules and/or NEEDS VERIFICATION rather than forced PASS/FAIL.

## 11. Core Compliance Rule Matrix
| ID | Module | Machine-check / decision | Outcome | Legal reference |
|---|---|---|---|---|
| R-APP-01 | Applicability | Check whether Chapter II retail-package provisions apply; package quantity/channel/consumer type determine applicability. | PASS / NOT APPLICABLE / VERIFY | Rule 3 |
| R-APP-02 | Retail package classification | Classify retail package, wholesale package, industrial/institutional package and imported package. | VERIFY | Definitions + Rule 3 |
| R-APP-03 | Quantity threshold | Flag packages over 25 kg or 25 litre where Chapter II exclusion may apply; special cement/fertilizer/agricultural produce treatment must be represented. | VERIFY | Rule 3 |
| R-APP-04 | Industrial/institutional | Flag declared/not-for-retail-sale context and avoid applying retail rules blindly. | VERIFY | Rule 3 + definitions |
| R-DECL-01 | Manufacturer/packer/importer | Name/address declaration as applicable. | REQUIRED / VERIFY | Rule 6(1)(a) |
| R-DECL-02 | Country of origin | Imported products must carry country of origin/manufacture/assembly as applicable. | REQUIRED / VERIFY | Rule 6(1)(aa) |
| R-DECL-03 | Common/generic name | Common or generic name of commodity must be present. | REQUIRED | Rule 6(1)(b) |
| R-DECL-04 | Multiple products | Packages containing more than one product must identify each product and its number/quantity as applicable. | REQUIRED / VERIFY | Rule 6(1)(b) |
| R-DECL-05 | Net quantity | Net quantity by standard unit of weight/measure or by number where applicable. | REQUIRED | Rule 6(1)(c) |
| R-DECL-06 | Manufacture/pre-pack/import date | Month and year as applicable, subject to exceptions/other-law provisions. | REQUIRED / VERIFY | Rule 6(1)(d) |
| R-DECL-07 | Best-before/use-by | Where commodity may become unfit after a period, relevant best-before/use-by declaration unless another law governs. | CONDITIONAL | Rule 6(1)(da) |
| R-DECL-08 | MRP | Retail sale price / maximum retail price inclusive of all taxes, in rupees/paise with prescribed rounding convention. | REQUIRED / VERIFY | Rule 6(1)(e) |
| R-DECL-09 | Dimensions | Where sizes/dimensions are relevant, dimensions of commodity and differing pieces as applicable. | CONDITIONAL | Rule 6(1)(f) |
| R-DECL-10 | Consumer contact | Name, address, telephone and e-mail of contact/person/office for complaints. | REQUIRED / VERIFY | Rule 6(2) |
| R-DECL-11 | Sticker restrictions | Detect stickers that appear to alter mandatory declarations; reduced MRP sticker is a special permitted case subject to conditions. | FLAG / VERIFY | Rule 6(3) |
| R-DECL-12 | Additional codes | Barcode/GTIN/QR code/e-code and authorized government logos may be added subject to rules. | INFO | Rule 6(4A) |
| R-DECL-13 | Multi-unit package | Declarations may need to appear on main package and/or individual accompanying packages according to structure. | CONDITIONAL | Rule 6(5) |
| R-DECL-14 | GM food | If applicable, package may require GM marking at top of principal display panel. | CONDITIONAL | Rule 6(7) |
| R-DECL-15 | Vegetarian/non-vegetarian marking | For specified soap, shampoo, toothpaste, cosmetics/toiletries provision, detect applicable marking and route to verification. | CONDITIONAL | Rule 6(8) |
| R-DECL-16 | Unit sale price | Where applicable, display unit sale price using prescribed unit formats. | REQUIRED / VERIFY | Rule 6(11) and amendments |
| R-PLACE-01 | Principal display panel | Verify declarations are located as required and can be grouped in the permitted manner. | VERIFY | Definitions/Rule 6 |
| R-READ-01 | Legibility | Text must be readable; low-confidence/obscured declarations go to verification. | VERIFY | Rule 8 + applicable provisions |
| R-READ-02 | Character height | Estimate minimum character height using calibrated image measurement where possible. | VERIFY | Rule 7 |
| R-READ-03 | Character width | Flag if character width is less than one-third of character height, excluding specified character exceptions. | VERIFY | Rule 7 |
| R-QTY-01 | Unit consistency | Normalize quantity and unit; detect missing/invalid/ambiguous unit. | REQUIRED / VERIFY | Rule 6 + units |
| R-QTY-02 | Quantity accuracy | Where actual measured quantity is available, compare against applicable maximum permissible error schedule; otherwise do not infer actual quantity from label alone. | VERIFY | Rule 9 / First Schedule |
| R-SPECIAL-01 | Promotional group package | Every retail package in a promotional group must comply with Rule 6. | REQUIRED / VERIFY | Rule 5(2) |
| R-SPECIAL-02 | Standard pack sizes | For commodities subject to standard quantities, check applicable schedule/notification; flag non-standard situations for legal verification. | VERIFY | Rule 5 + Second Schedule |
| R-SPECIAL-03 | Garments/hosiery | Apply special garment/hosiery provisions only when category/packaging conditions match. | CONDITIONAL | 2022 amendments + applicable guidance |
| R-SPECIAL-04 | Food/cosmetics/medical devices | Apply cross-law treatment and category-specific provisions; do not duplicate requirements incorrectly. | VERIFY | Rule 6 explanations + applicable sector law |
| R-ECOM-01 | E-commerce information | Compare listing declarations with physical package information where listing evidence is supplied. | VERIFY | Applicable PCR e-commerce provisions |
| R-ECOM-02 | Imported product origin filter | Track e-commerce country-of-origin filter requirement by its effective date and latest amendment. | VERIFY / CONFIGURABLE | 2026 amendments |
| R-PRICE-01 | Sale above MRP | If transaction/sale evidence exists, flag sale price above declared retail sale price for officer review. | FLAG / VERIFY | Rule 18(2) |
| R-VERSION-01 | Effective date | Select rules based on inspection date and rule effective_from/effective_to. | SYSTEM | Rule governance |
| R-VERSION-02 | Source traceability | Every automated legal finding must retain source notification/rule version. | SYSTEM | Governance |

## 12. Mandatory Declaration Extraction Schema
| Field | Meaning | Extraction | Target confidence |
|---|---|---|---|
| product_name | Common/generic name | OCR + semantic extraction | High |
| manufacturer_name | Manufacturer name | OCR + pattern/context | High |
| manufacturer_address | Manufacturer address | OCR + address block | Medium/High |
| packer_name | Packer name | OCR + context | High |
| packer_address | Packer address | OCR + context | Medium/High |
| importer_name | Importer name | OCR + context | High |
| importer_address | Importer address | OCR + context | Medium/High |
| country_of_origin | Country of origin/manufacture/assembly | OCR + country dictionary | High |
| net_quantity | Quantity number | OCR + quantity parser | High |
| net_unit | g/kg/ml/l/cm/m/number/etc. | OCR + unit parser | High |
| mrp | MRP amount | Pattern + currency parser | High |
| mrp_tax_inclusive | Inclusive of all taxes indication | Pattern/semantic | Medium |
| unit_sale_price | Unit sale price | Pattern + arithmetic/context | Medium/High |
| manufacture_month | Month | Date parser | Medium |
| manufacture_year | Year | Date parser | Medium |
| best_before | Best before/use-by | Date/duration parser | Medium |
| consumer_contact_name | Complaint contact | OCR/context | Medium |
| consumer_phone | Telephone | Regex | High |
| consumer_email | Email | Regex | High |
| dimensions | Commodity dimensions | OCR/structured parser | Medium |
| barcode_gtin_qr | Barcode/GTIN/QR presence | CV/barcode reader | High |
| gm_marking | GM marking where applicable | CV/OCR | Medium |
| veg_nonveg_marking | Specified marking where applicable | CV/OCR | Medium |
| not_for_retail_sale | Institutional/industrial indicator | OCR | High |

## 13. Unit Sale Price Rules
Implement unit sale price as a dedicated normalized object rather than free text. The 2021 amendments specify unit-price formats including weight, length, number and volume thresholds.
| Commodity basis | Unit-sale representation to validate |
|---|---|
| Weight < 1 kg | Rs per g |
| Weight ≥ 1 kg | Rs per kg |
| Length < 1 m | Rs per cm |
| Length ≥ 1 m | Rs per metre |
| Sold by number | Rs per number |
| Volume < 1 L | Rs per ml |
| Volume ≥ 1 L | Rs per litre |

The engine should parse the declared unit sale price, derive the expected unit from net quantity, and flag mismatches. It should not invent a unit sale price when the legal applicability cannot be established.

## 14. MRP Validation
- Recognize MRP, M.R.P., Maximum Retail Price and common currency variants.
- Extract numeric value and currency context.
- Normalize comma/decimal formats.
- Detect whether the label states inclusive of all taxes or an accepted equivalent.
- Preserve the original OCR span as evidence.
- Compare physical package MRP with listing MRP only as a potential inconsistency; require review before legal conclusion.
- If sale-price evidence is available, flag transaction price above declared MRP for officer review.
- Handle permitted lower-MRP sticker scenario separately rather than treating every sticker as a violation.

## 15. Net Quantity and Quantity Accuracy
- Separate numeric quantity from unit.
- Normalize kg↔g, L↔ml and other supported conversions without changing the source declaration.
- Detect number-based packages such as pieces/units/pairs/sets where applicable.
- Use category-specific rules where a commodity is sold by number or another prescribed basis.
- Do not infer actual physical quantity from a photograph.
- If a calibrated weighing/measuring result is entered by an inspector, run maximum-permissible-error checks using the configured First Schedule data.
- Store the measurement device/result as separate evidence.

## 16. Character Height / Font-Size Inspection
A normal photo does not reliably provide millimetres. The MVP therefore uses an explicit calibration method.
- Inspector enters one known package dimension in millimetres (for example, measured package width).
- CV detects the same dimension in pixels.
- Compute pixels-per-mm = detected_pixel_dimension / known_mm_dimension.
- Detect text/character bounding boxes and estimate character height in pixels.
- Convert height_px / pixels_per_mm into estimated millimetres.
- Determine principal-display-panel area where feasible or capture it as inspector input.
- Load the applicable minimum character-height threshold from Rule 7.
- Return PASS only when image quality and calibration confidence are adequate; otherwise return NEEDS VERIFICATION.

| Principal display panel area | Minimum height: printed/typed | Minimum height: molded/blown/formed |
|---|---|---|
| ≤ 50 cm² | 1.0 mm | 1.5 mm |
| > 50 to ≤100 cm² | 1.5 mm | 3.0 mm |
| > 100 to ≤500 cm² | 2.5 mm | 4.0 mm |
| > 500 to ≤2500 cm² | 4.0 mm | 6.0 mm |
| > 2500 cm² | 6.0 mm | 6.0 mm |

The character-width requirement is represented as a separate check: width should not be less than one-third of height, subject to the rule's stated exception for the characters 1, i, I and l. Measurement uncertainty must be surfaced to the reviewer.

## 17. Readability and Placement
- Detect text obscured by glare, folds, seals, graphics, low contrast or crop.
- Detect whether mandatory fields appear on a permitted principal display panel/label region.
- Use OCR confidence plus visual contrast/blur metrics as supporting evidence, not as a legal conclusion by themselves.
- Provide a manual 'Readable / Not readable / Needs verification' control.
- Allow the reviewer to draw or adjust the evidence bounding box.

## 18. Applicability and Exemption Engine
The engine must evaluate applicability before evaluating a requirement. This avoids false positives caused by applying a general rule to a special category.
| Input | Examples |
|---|---|
| Inspection date | 2026-09-04 |
| Commodity category | food, cosmetics, garment, household item, agricultural produce |
| Package quantity | 500 g, 2 kg, 10 L, etc. |
| Channel | retail store, e-commerce, institutional, industrial |
| Origin | domestic/imported |
| Package structure | single, multi-product, promotional group |
| Special status | GM food, garment/hosiery, medical device, etc. |
| Other-law control | FSSAI/cosmetics/sector-specific regime where applicable |
| Evidence quality | adequate / inadequate |

Every rule record therefore needs an applicability expression or structured conditions. Exemptions are explicit objects, not hidden exceptions in code.

## 19. Rule Engine Design
The rule engine is deterministic and versioned. A language model can assist with extraction or explanation but cannot create a new legal rule.
| Rule object | Purpose |
|---|---|
| rule_id | Stable internal identifier |
| rule_number | Legal rule/sub-rule reference |
| title | Human-readable title |
| description | Validation statement |
| conditions | Structured applicability conditions |
| validation_type | presence, pattern, arithmetic, measurement, comparison, manual |
| parameters | Thresholds, units, patterns |
| severity | info, low, medium, high, critical |
| effective_from | Date rule becomes applicable |
| effective_to | Date rule stops applying, if known |
| source_document | Official notification/rules source |
| source_locator | Page/section/sub-rule locator |
| version | Ruleset version |
| review_status | draft/test/published/retired |

## 20. Example Rule Object
Example JSON concept: `{"rule_id":"R-DECL-05","rule_number":"6(1)(c)","validation_type":"required_field","field":"net_quantity","applicability":{"chapter":"II","retail_package":true},"outcomes":{"missing":"potential_non_compliance","low_confidence":"needs_verification"},"source":"Legal Metrology (Packaged Commodities) Rules, 2011","version":"PCR-2026.x"}`

## 21. Assessment State Machine
| Stage | State | Meaning |
|---|---|---|
| Automated | PASS | Automated check satisfied with adequate evidence. |
| Automated | POTENTIAL NON-COMPLIANCE | Potential issue detected; not a final legal conclusion. |
| Automated | NEEDS VERIFICATION | Evidence or applicability is insufficient. |
| Human | CONFIRMED | Authorized reviewer confirms finding. |
| Human | REJECTED | Reviewer rejects automated finding. |
| Human | MANUAL VERIFICATION | Requires measurement/document/inspection outside automation. |
| Final | CLOSED | Inspection finalized with audit trail. |

## 22. Evidence Model
- Original image ID and SHA-256 hash.
- Processed image ID.
- OCR block ID and text.
- Bounding box x/y/width/height.
- Field ID and normalized value.
- Rule ID and ruleset version.
- Automated result and confidence.
- Reviewer status, reviewer ID and timestamp.
- Comment and optional corrected value.
- Report reference.

## 23. AI / Computer Vision Pipeline
1. Image ingestion.
2. Quality scoring.
3. Perspective/orientation correction.
4. Text-region detection.
5. OCR.
6. OCR confidence filtering.
7. Entity/field extraction.
8. Normalization.
9. Category classification.
10. Deterministic rules execution.
11. Evidence generation.
12. Optional LLM explanation grounded only in retrieved official rules.
Recommended MVP OCR: PaddleOCR. Recommended image processing: OpenCV. Optional object/text-region detector: YOLO-family model. Optional multimodal model: fallback only for ambiguous extraction, with human review.

## 24. OCR Error Handling
- Run OCR on original and enhanced image variants when confidence is low.
- Merge overlapping OCR boxes carefully.
- Keep raw OCR and normalized value separate.
- Use dictionaries for units, months, country names and common declaration labels.
- Use regex for phone/email/currency/date candidates.
- Never silently overwrite low-confidence text; show alternatives.
- Allow inspector correction and preserve original OCR.

## 25. Category Detection
Category should be suggested, not silently fixed. Use product name + OCR keywords + visual signals + inspector confirmation.
- Food and beverage
- Cosmetics/toiletries
- Household goods
- Garments/hosiery
- Stationery
- Electrical/electronic consumer goods
- Imported goods
- Agricultural/farm produce
- Medical-device-related packages
- Other / custom

## 26. E-Commerce Extension
- Accept listing URL where permitted and available.
- Provide screenshot upload as reliable fallback.
- Extract product title, brand, seller/manufacturer/importer, MRP, selling price, net quantity, origin and listing images.
- Compare listing fields with physical-package fields.
- Flag missing or inconsistent data for review.
- Track country-of-origin filter capability as a configurable requirement with effective date from the latest applicable amendment.
- Do not rely on scraping for the hackathon MVP.

## 27. Database Schema
| Table | Core columns |
|---|---|
| users | id, name, role, email, status, created_at |
| inspections | id, inspector_id, location, channel, inspection_date, category, status, ruleset_version, created_at |
| products | id, name, brand, category, manufacturer, origin, first_seen_at |
| inspection_images | id, inspection_id, type, original_url, processed_url, sha256, width, height |
| ocr_blocks | id, image_id, text, confidence, x, y, width, height |
| extracted_fields | id, inspection_id, field_name, raw_value, normalized_value, confidence, source_ocr_ids |
| rules | id, rule_id, rule_number, title, conditions_json, validation_json, effective_from, effective_to, source, version, status |
| assessments | id, inspection_id, rule_id, result, confidence, explanation, created_at |
| findings | id, assessment_id, severity, status, evidence_image_id, bbox_json, reviewer_id, reviewer_comment |
| measurements | id, inspection_id, type, value, unit, method, device_note, evidence_id |
| reports | id, inspection_id, pdf_url, editable_url, generated_at |
| audit_logs | id, actor_id, action, entity_type, entity_id, before_json, after_json, timestamp |

## 28. API Design
| Method | Endpoint | Purpose |
|---|---|---|
| POST | /auth/login | Authenticate |
| POST | /inspections | Create inspection |
| POST | /inspections/{id}/images | Upload evidence |
| POST | /inspections/{id}/process | Run OCR/CV pipeline |
| GET | /inspections/{id} | Get inspection |
| GET | /inspections/{id}/fields | Get extracted fields |
| POST | /inspections/{id}/assess | Run rules |
| PATCH | /findings/{id} | Review/confirm/reject |
| POST | /inspections/{id}/report | Generate report |
| GET | /inspections | Search history |
| GET | /dashboard | Analytics |
| GET | /rules | List rules |
| POST | /rules | Create rule version |
| POST | /rules/{id}/publish | Publish ruleset |

## 29. Recommended Technology Stack
| Layer | Recommended choice | Reason |
|---|---|---|
| Frontend | Next.js + React + Tailwind CSS | Fast dashboard and responsive UI |
| Backend | FastAPI + Python | Excellent OCR/CV/rules ecosystem |
| OCR | PaddleOCR | Strong multilingual/document OCR option |
| CV | OpenCV + optional YOLO | Preprocessing and region detection |
| Database | PostgreSQL | Structured, auditable relational data |
| Storage | S3-compatible / Supabase Storage | Private image/report storage |
| Rules | Python + PostgreSQL/JSON | Versioned deterministic validation |
| Auth | JWT/OAuth or managed auth | RBAC |
| Reports | ReportLab + python-docx | PDF + editable report |
| Deployment | Vercel frontend + Render/Railway/AWS backend | Hackathon-friendly |
| Queue | Redis + Celery/RQ optional | Long OCR jobs |

## 30. UI / Screen Specification
| ID | Screen | Key elements |
|---|---|---|
| S01 | Login | Email/password or SSO; role-aware landing. |
| S02 | Dashboard | Inspection counts, status, categories, trends. |
| S03 | New Inspection | Metadata + category + channel + date. |
| S04 | Evidence Capture | Multi-image upload/camera; image quality warnings. |
| S05 | Processing | Progress through quality, OCR, extraction and rules. |
| S06 | Assessment | Image viewer + fields + compliance matrix. |
| S07 | Evidence Viewer | Zoom, bounding boxes, OCR text and rule evidence. |
| S08 | Review | Confirm/reject/manual verification controls. |
| S09 | Report | Preview, export PDF/editable. |
| S10 | History | Search/filter/sort inspections. |
| S11 | Product Detail | Historical inspection findings. |
| S12 | Rule Admin | Ruleset versions, effective dates and source. |

## 31. Assessment Screen Wireframe
LEFT: package image viewer with zoom, rotate and evidence overlays.
CENTER: extracted declarations with raw value → normalized value → confidence.
RIGHT: rule assessment cards: Rule ID, requirement, result, evidence, confidence, reviewer controls.
TOP: inspection ID, category, channel, date, ruleset version.
BOTTOM: Save review | Generate report | Close inspection.

## 32. Dashboard KPIs
- Total inspections
- Compliant / PASS
- Potential non-compliance
- Needs verification
- Confirmed findings
- Top finding categories
- Average processing time
- OCR field extraction accuracy
- Reviewer confirmation rate
- Inspections by category/channel/location
- Trend by week/month

## 33. Report Specification
Report sections: inspection metadata; product identity; evidence list; extracted declarations; rule applicability; assessment table; findings; image evidence; reviewer decisions; ruleset/source version; timestamps; signature/approval fields.
| Report column | Content |
|---|---|
| Rule | Rule ID + legal rule number |
| Requirement | Plain-language check |
| Observed | Extracted/observed value |
| Result | PASS / Potential Non-Compliance / Needs Verification / Confirmed |
| Evidence | Image + bounding box reference |
| Confidence | OCR/measurement confidence |
| Reviewer | Name/ID and timestamp |
| Remarks | Manual notes |

## 34. Security and Privacy
- HTTPS/TLS in transit.
- Encrypted storage where supported.
- Private object storage and signed access URLs.
- RBAC and least privilege.
- File-type, size and malware validation.
- Original evidence immutable after inspection closure.
- Audit logs for review, rule changes and report generation.
- Do not expose private inspection images through public URLs.
- Configurable retention/deletion policy.
- Rule publication restricted to authorized administrators.

## 35. Explainability Principles
- Show the exact rule that was evaluated.
- Show why the rule was applicable.
- Show the extracted value used.
- Show the image evidence.
- Show confidence and uncertainty.
- Show the ruleset version/effective date.
- Show human review outcome separately from automated outcome.
- Never write 'illegal' solely from an LLM response.

## 36. LLM / RAG Legal Assistant
Optional assistant: 'Why was this flagged?' retrieves the relevant approved official rule text/source and explains the finding. Retrieval is constrained to the organization's approved legal corpus. The LLM may summarize and explain; it may not add requirements not present in the retrieved source.
- Approved source list only.
- Chunk official rules/notifications by rule/sub-rule.
- Store source metadata and effective date.
- Retrieve by rule ID first; semantic retrieval second.
- Cite source in explanation.
- Fallback to 'Needs legal verification' when retrieval is ambiguous.

## 37. Rule Governance
1. Admin imports official notification/source.
2. System stores source document metadata.
3. Rule analyst creates/updates structured rule.
4. Automated tests run against known examples.
5. Second reviewer approves.
6. Ruleset receives version and effective date.
7. Published ruleset becomes immutable.
8. Future amendment creates a new version; old inspections retain historical version.

## 38. Testing Strategy
| Test type | Examples |
|---|---|
| Unit | MRP parser, unit parser, date parser, country parser |
| Rule unit tests | Missing manufacturer, invalid MRP, missing net quantity, unit sale price mismatch |
| Applicability | 25 kg threshold, institutional package, imported package, special category |
| OCR integration | Blurred/rotated/multilingual labels |
| CV | Perspective correction, glare and bounding boxes |
| Measurement | Calibration and font-size threshold fixtures |
| API | Auth, upload, assessment, report, rules |
| UI | Upload, review, evidence, export |
| E2E | Image → OCR → rules → review → report |
| Security | RBAC, invalid files, unauthorized evidence access |

## 39. Quality Metrics
- Field extraction accuracy
- MRP extraction precision
- Net-quantity extraction precision
- Mandatory-field detection recall
- Potential-issue precision
- Evidence coverage (% findings with evidence)
- Average processing time per inspection
- Needs-verification rate
- Human-review agreement with automated assessment
- Report generation success rate

## 40. MVP Scope for SIH
| Priority | Features |
|---|---|
| P0 | Auth, inspection creation, multi-image upload, quality gate, preprocessing, OCR, field extraction, category confirmation, core rules, evidence overlays, review, PDF/editable report, history, dashboard |
| P1 | Calibrated character-size estimate, multilingual OCR, duplicate detection, richer analytics, product history |
| P2 | E-commerce screenshots/URL ingestion, barcode/GTIN, advanced placement detection, offline mode |
| P3 | Tamper/anomaly analytics, integrations, mobile app, large-scale model optimization |

## 41. Demo Dataset
| Demo case | Expected behavior |
|---|---|
| Case A — compliant label | Most core fields found; PASS where evidence is adequate. |
| Case B — missing declaration | Field missing; POTENTIAL NON-COMPLIANCE with highlighted evidence/context. |
| Case C — unreadable/tiny declaration | OCR confidence/measurement insufficient; NEEDS VERIFICATION. |
| Case D — imported package | Country of origin and importer fields checked. |
| Case E — e-commerce mismatch | Listing and physical package fields compared; mismatch flagged for review. |

## 42. 5-Minute Hackathon Demo Script
- 0:00–0:30 — State the manual-inspection problem.
- 0:30–1:00 — Open MitraMetrology and create inspection.
- 1:00–1:30 — Upload front/back package images.
- 1:30–2:15 — Show image quality, OCR and extracted declarations.
- 2:15–3:15 — Run versioned rules engine and show PASS / Potential Issue / Needs Verification.
- 3:15–4:00 — Click a finding and show exact image evidence + rule reference.
- 4:00–4:30 — Human confirms/rejects finding.
- 4:30–5:00 — Generate report and show dashboard/history.

## 43. 48-Hour Build Plan
| Time | Work |
|---|---|
| 0–4 h | Repo, architecture, DB, auth, basic UI |
| 4–10 h | Inspection creation, image upload, storage, metadata |
| 10–18 h | OpenCV preprocessing + OCR pipeline |
| 18–24 h | Field extraction + normalization |
| 24–30 h | Rules engine + core rule dataset |
| 30–34 h | Evidence overlay + assessment UI |
| 34–38 h | PDF/editable report |
| 38–42 h | History + dashboard |
| 42–46 h | Testing, error states, security hardening |
| 46–48 h | Demo data, UI polish, pitch rehearsal |

## 44. Team Split
| Member | Ownership |
|---|---|
| Member 1 | Frontend + assessment UI |
| Member 2 | Backend + database + APIs |
| Member 3 | OCR/CV + image pipeline |
| Member 4 | Rules engine + legal data model |
| Member 5 (optional) | Reports + dashboard + deployment/demo |

## 45. Risks and Mitigations
| Risk | Mitigation |
|---|---|
| OCR errors | Multi-pass OCR, confidence thresholds, manual correction |
| Curved/angled labels | Perspective correction + retake guidance |
| Tiny text | Close-up capture + calibrated measurement + manual verification |
| Legal amendments | Versioned rule database + effective dates |
| False positives | Applicability engine + NEEDS VERIFICATION state |
| LLM hallucination | Deterministic rule engine + RAG-only explanation |
| E-commerce scraping failure | Screenshot upload fallback |
| Privacy | Private storage + RBAC + audit logs |
| Overclaiming automation | Human confirmation before final legal conclusion |

## 46. Definition of Done
- A user can create an inspection and upload multiple package images.
- The system rejects or warns on poor image quality.
- OCR returns text and bounding boxes.
- Core declarations are extracted and normalized.
- Rules are versioned and date-aware.
- At least the core declaration, MRP, unit sale price, origin, contact, readability and measurement workflows are implemented.
- Every potential finding has evidence and rule metadata.
- Reviewer can confirm/reject/manual-verify.
- PDF and editable report are generated.
- Inspection is searchable after closure.
- Dashboard reflects inspection outcomes.
- No automated result is presented as a final legal enforcement decision.

## 47. Official Legal Sources and Research Basis
Primary source: Department of Consumer Affairs, Government of India — Legal Metrology Act / Packaged Commodities Rules page. The official page lists the 2011 rules and subsequent amendments, including 2022, 2023, 2025 and 2026 amendments.
Official Department page: https://consumeraffairs.gov.in/pages/legal-metrology-act
Department 'What's New' page with the book on Packaged Commodities Rules and FAQs: https://consumeraffairs.nic.in/whats-new-0
Rajasthan government consolidated rules PDF used as a practical text reference: https://swcs.rajasthan.gov.in/Upload/ce69e6c9-9deb-46d9-a981-858d9df602c1Legal%20Metrology%20(Packaged%20commodity)%20Rules%202011.pdf
Important: the product should ship with a maintained official-source register. Before production or real enforcement use, the legal team must validate every configured rule against the latest Gazette/Department notification and applicable sector-specific law.

## 48. Current Amendment Handling (2025–2026)
The Department's current Legal Metrology page lists Packaged Commodities amendments dated 24.10.2025, 02.12.2025, 13.02.2026, a Second Amendment 2026 and a Third Amendment 2026 dated 29.05.2026. The rules engine should therefore not hard-code a single 2011 checklist.
For the e-commerce country-of-origin filter, the system must use the latest applicable amendment/effective date in its rule configuration. Do not hard-code an older date when a later amendment changes commencement.

## 49. Legal Caveats
- This PRD is an engineering specification, not legal advice.
- The phrase 'Potential Non-Compliance' is intentionally used for automated findings.
- Some requirements are controlled by other laws/rules or have exemptions; the engine must model those conditions.
- Actual quantity deficiency requires a valid measurement process; a photo cannot establish weight/volume accuracy.
- Font-size measurement from an image is an estimate unless calibrated and sufficiently captured.
- The system should retain the exact source notification/rule version used for every assessment.

## 50. Suggested Repository Structure
```
/mitrametrology
  /frontend
    /app
    /components
    /features/inspection
    /features/assessment
    /features/dashboard
  /backend
    /api
    /models
    /services/ocr
    /services/cv
    /services/extraction
    /services/rules
    /services/reports
  /rules
    /sources
    /versions
    /tests
  /ml
    /ocr
    /detectors
  /docs
    /legal
    /architecture
  /tests
  docker-compose.yml
```

## 51. Recommended Initial Rule IDs
Seed the database with stable IDs so the UI and reports remain consistent across amendments.
| ID prefix | Module |
|---|---|
| R-APP | Applicability and exemptions |
| R-DECL | Mandatory declarations |
| R-PRICE | MRP/sale-price checks |
| R-UNIT | Unit sale price/unit normalization |
| R-QTY | Net quantity/measurement |
| R-DATE | Date declarations |
| R-CONTACT | Consumer-care contact |
| R-PLACE | Placement/principal display panel |
| R-READ | Readability/character size |
| R-SPECIAL | Category/special-package rules |
| R-ECOM | E-commerce |
| R-VERSION | Ruleset governance |

## 52. Final Product Principle
The strongest SIH solution is not 'AI that decides the law'. It is an evidence-backed compliance assistant where AI reads and locates information, deterministic rules apply the law, uncertainty is explicit, and a human officer remains in control of the final determination.
MitraMetrology AI = Capture → Understand → Apply → Prove → Review → Report.

*END OF PRD*