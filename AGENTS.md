# MitraMetrology AI — AGENTS.md

Master plan + conventions for this repo. Auto-loaded every session. Read this before any work.

## Project
- **Product**: MitraMetrology AI — SIH problem statement 26034 (Legal Metrology (Packaged Commodities) Rules, 2011)
- **Tagline**: Scan. Verify. Explain. Enforce.
- **Vision**: Capture → Understand → Apply → Prove → Review → Report (evidence-backed compliance assistant)
- **Full spec**: `docs/prd/PRD.md` (approved PRD v2.0, 04 Sep 2026)

## GOLDEN RULE (never break)
No automated result is ever a legal conclusion. The LLM/CV/OCR layer assists extraction/vision ONLY.
- Automated outcomes are ONLY: `PASS`, `POTENTIAL NON-COMPLIANCE`, `NEEDS VERIFICATION`, `NOT APPLICABLE`.
- A human reviewer confirms/rejects before anything is "legal": `CONFIRMED`, `REJECTED`, `MANUAL VERIFICATION`.
- Never write "illegal" / "violation" as a final verdict from automation alone (PRD §6, §21, §35, §52).
- Rules are versioned + effective-date aware; old inspections keep their historical ruleset version.
- Evidence-first: every finding must link to image + bbox + OCR span + rule id/version + confidence (PRD §22).

## Scope (MVP P0, PRD §40)
Auth, inspection creation, multi-image upload, quality gate, preprocessing, OCR, field extraction, category confirmation, core rules, evidence overlays, human review, PDF/editable report, history, dashboard.
**Deferred**: calibrated font-size measurement, e-commerce URL ingestion, barcode/GTIN, advanced placement, RAG assistant, offline. (P1–P3)

## Environment facts (verified)
- OS: Windows 11, PowerShell 5.1. Shells: powershell. No Docker.
- Python 3.13.0 (pip 26.1.2, user site: `C:\Users\shaki\AppData\Roaming\Python\Python313`)
- Node v24.12.0, npm 11.6.2
- PostgreSQL 17.6 via conda base env: binaries at `C:\Users\shaki\anaconda3\Library\bin` (psql, pg_ctl, initdb, postgres). `pg_config` on PATH = anaconda's (was stale/incomplete pre-install — now real).
- Postgres local dev server: data dir `C:\Users\shaki\pgdata\mitrametrology` (OUTSIDE OneDrive-synced workspace), trust auth, superuser `postgres`, port 5432. Start/stop via `scripts/pg-local.ps1 [init|start|stop|status]`.
- IMPORTANT: connect with `127.0.0.1` (IPv4). Do NOT use `localhost` for psql/SQLAlchemy — IPv6 (::1) triggers a GSSAPI credential error. DB name: `mitrametrology`. URL: `postgresql+psycopg2://postgres@127.0.0.1:5432/mitrametrology`.
- PaddleOCR 3.7.0 + PaddlePaddle **pinned to 3.2.2** (verified working on Python 3.13 CPU). DO NOT upgrade paddlepaddle to 3.3.x — its PIR/oneDNN path crashes CPU inference with `NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support`. Models cached in user profile by first run (`scripts/download_ocr_models.py`).
- Verify OCR stack: `backend/.venv\Scripts\python.exe scripts\ocr_smoke.py` (models cached at `C:\Users\shaki\.paddlex\official_models\PP-OCRv6_medium_{det,rec}`)
- Working dir: `C:\Users\shaki\OneDrive\Desktop\LabelGuard`

## Shared contracts (lock before feature work)
| ID | Owner | Content |
|---|---|---|
| C-1 API spec | A | Endpoints + JSON shapes per PRD §28 |
| C-2 DB schema | A | SQLAlchemy models per PRD §27 |
| C-3 Rule JSON v1 | B | Schema per PRD §19–20; seed `rules/versions/seed_rules_v1.json` |
| C-4 Extraction schema | B | Field list PRD §12 + normalized value JSON |
| C-5 Assessment model | B | PASS/POTENTIAL/NEEEDS/NA + evidence links (PRD §21–22) |

Contracts are LOCKED at Phase 0 and live in `docs/contracts/` (C1-api.md, C2-db-schema.md, C3-rule-json.md, C4-extraction-schema.md, C5-assessment-model.md). Feature work must match them.

## Team split (3 people)
| Person | Owns | Deliverables |
|---|---|---|
| **A — Backend & DB** | FastAPI, PostgreSQL, auth/RBAC, storage, orchestration APIs, audit | All `/api/*` routes working on real data; C-1, C-2 |
| **B — CV/OCR + Rules** | OpenCV, PaddleOCR, extraction/normalization, versioned rules engine, evidence | Quality gate → OCR → fields → assessments; C-3, C-4, C-5 |
| **C — Frontend + Reports** | Next.js S01–S12, assessment 3-pane, evidence viewer, PDF/docx, dashboard | Demo-facing product + reports |

B alone edits rule JSON / legal data. A owns repo integration. C owns presentation fidelity.

## Build plan (48h, three tracks)
- **Phase 0 (0–4h, all)**: scaffold (this file, PRD archive, README, git init, folder tree); A: DB + FastAPI skeleton; B: PaddleOCR/OpenCV install + model download (longest); C: create-next-app + Tailwind + route stubs; lock C-1..C-5 in `docs/contracts/`
- **A track**: A1 models 4–8h → A2 JWT+RBAC+audit 6–10h → A3 inspections+images upload/storage/SHA 8–12h → A4 process orchestrator 12–14h → A5 GETs + PATCH findings 14–18h → A6 report wiring/history/dashboard/rules 30–34h → A7 smoke+security 42–46h
- **B track**: B1 quality gate 4–8h → B2 preprocessing 8–12h → B3 PaddleOCR pass + merge 12–16h → B4 extraction + normalization (MRP §14, net qty §15, unit sale price §13, dates) 16–22h → B5 applicability engine §18 22–28h → B6 deterministic rules §11 28–32h → B7 evidence linkage §22 32–36h → B8 unit + rule tests 44–46h
- **C track**: C1 auth 4–8h → C2 new inspection + upload w/ quality warnings 8–12h → C3 processing screen 12–16h → C4 assessment 3-pane (S06/S07, PRD §31) 16–26h → C5 review controls (S08) 26–32h → C6 reports PDF+docx (S09, §33) 32–38h → C7 history + dashboard 38–42h → C8 E2E + polish 42–46h
- **Integration syncs**: h12, h24, h32 (process orchestrator A4↔B; assessment API A5↔C4; report A6↔C6)
- **Demo data (46–48h, all)**: seed Cases A–E (PRD §41) in `backend/seed/`; rehearse 5-min script (PRD §42)

## Core rule IDs to seed (stable, PRD §51)
R-APP (applicability), R-DECL (mandatory declarations), R-PRICE (MRP/sale price), R-UNIT (unit sale price), R-QTY (net qty/measurement), R-DATE, R-CONTACT, R-PLACE, R-READ, R-SPECIAL, R-ECOM, R-VERSION.
Core matrix to implement: PRD §11 (R-APP-01..04, R-DECL-01..16 subset, R-READ-01, R-QTY-01, R-PRICE-01, R-UNIT). Unit-sale-price basis table: PRD §13. MRP validation: PRD §14. Net qty: PRD §15.

## Repo structure
```
LabelGuard/
  AGENTS.md
  README.md
  docs/prd/PRD.md  docs/contracts/  docs/legal/sources.md
  backend/app/{main,config,db}.py {api,models,schemas,auth} services/{quality,preprocessing,ocr,extraction,rules,evidence,reports}.py seed/
  backend/tests/  tests/
  frontend/ (Next.js 16 + Tailwind; proxy.ts gates /dashboard)
  rules/versions/seed_rules_v1.json
  scripts/ (psql-setup, dev)
  ml/ocr/ ml/detectors/
```

## Commands
- Backend: `python -m venv backend/.venv` then `backend/.venv\Scripts\pip install ...`; run `backend/.venv\Scripts\uvicorn app.main:app --reload --port 8000`
- Run deps: fastapi, uvicorn, sqlalchemy, psycopg2-binary, pydantic, python-jose/PyJWT, passlib[bcrypt], python-multipart, Pillow, **opencv-contrib-python==4.10.0.84** (paddlex OCR-core pins this exact version — do NOT swap to plain opencv-python), paddleocr (paddlepaddle CPU), numpy, reportlab, python-docx, alembic, pytest, httpx
- Tests: `backend/.venv\Scripts\python -m pytest backend/tests`
- Demo seed (PRD §41): from backend/: `.venv\Scripts\python -m seed.demo_data [--reset]` (synthetic label images + scripted OCR bboxes → runs the REAL extraction/rules/evidence engine; outcomes deterministic)
- Cross-stack E2E (backend :8000 + built frontend :3000): `backend/.venv\Scripts\python -m pytest tests/e2e_flow.py -v`
- A-track live smoke: `backend/.venv\Scripts\python scripts\api_smoke.py` (29 checks: lifecycle, RBAC, review/close, category, reports)
- Frontend: `npm run dev` / `npm run build` / `npm run lint`
- Postgres (psql not on PATH): `& "C:\Users\shaki\anaconda3\Library\bin\psql" -U postgres -h 127.0.0.1 ...` or `.\scripts\pg-local.ps1 status`
- Backend smoke test: start uvicorn in backend/, then `Invoke-RestMethod http://127.0.0.1:8000/health`
- Lint/typecheck: `npm run lint` for frontend (Next 16; ESLint flat config) runs clean; typecheck via `npm run build`.

## Golden-rule enforcement in code
- Assessment state machine (PRD §21) is enforced in the rules service (B), surfaced in UI labels (C), never bypassed by API (A).
- Applicability evaluated BEFORE any check (PRD §18) to avoid false positives.
- Original images immutable; processed images derived; SHA-256 on originals (PRD §22, §34).
- Raw OCR and normalized value are separate fields; never silently overwrite low-confidence text (PRD §24).

## Legal sources register
Maintain `docs/legal/sources.md` with official URLs:
- https://consumeraffairs.gov.in/pages/legal-metrology-act
- https://consumeraffairs.nic.in/whats-new-0
- Also track 2025–2026 amendments (24.10.2025, 02.12.2025, 13.02.2026, 2nd & 3rd Amend. 2026 29.05.2026). Rules engine must use latest applicable effective date — never hard-code a stale checklist (PRD §48).