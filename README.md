# MitraMetrology AI

**Scan. Verify. Explain. Enforce.** — Evidence-backed compliance assistant for SIH Problem Statement 26034 (Legal Metrology (Packaged Commodities) Rules, 2011).

## What it does
An inspector uploads/captures package images → quality gate → OCR/CV → structured declarations → versioned deterministic rule engine → evidence-linked findings → human review → PDF/editable report → history & dashboard.

Automated outcomes are only `PASS`, `POTENTIAL NON-COMPLIANCE`, `NEEDS VERIFICATION`, `NOT APPLICABLE` — a human reviewer confirms the final legal conclusion.

## Docs
- Plan + conventions: `AGENTS.md`
- Full spec: `docs/prd/PRD.md`
- Legal source register: `docs/legal/sources.md`

## Layout
- `backend/` — FastAPI + PostgreSQL + OpenCV + PaddleOCR + rules engine
- `frontend/` — Next.js 15 + Tailwind (S01–S12)
- `rules/versions/` — versioned rule JSON seeds
- `scripts/` — psql setup + dev scripts
- `tests/` — cross-stack tests

## Quick start
See `AGENTS.md` → Commands (backend venv, uvicorn, `npm run dev`, psql via `pg_config`). No Docker; Windows-first environment.