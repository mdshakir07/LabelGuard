# LabelGuard

**Scan. Verify. Explain. Enforce.** — Evidence-backed compliance assistant for SIH Problem Statement 26034 (Legal Metrology (Packaged Commodities) Rules, 2011).

## What it does
An inspector uploads/captures package images → quality gate → OCR/CV → structured declarations → versioned deterministic rule engine → evidence-linked findings → human review → PDF/editable report → history & dashboard.

Automated outcomes are only `PASS`, `POTENTIAL NON-COMPLIANCE`, `NEEDS VERIFICATION`, `NOT APPLICABLE` — a human reviewer confirms/rejects/requests manual verification before any legal conclusion (golden rule, PRD §21).

## Docs
- Plan + conventions: `AGENTS.md`
- Full spec: `docs/prd/PRD.md`
- Locked contracts (C-1..C-5): `docs/contracts/`
- Legal source register: `docs/legal/sources.md`

## Layout
- `backend/app` — FastAPI + PostgreSQL + OpenCV + PaddleOCR + rules engine `services/`
- `backend/seed` — default users/rules (`seed.py`) + demo dataset Cases A–E (`demo_data.py`)
- `backend/tests` — unit tests (controllers, services, category)
- `frontend/` — Next.js 16 + Tailwind, all S01–S12 screens; `proxy.ts` (Next 16 middleware) gates `/dashboard` etc.
- `rules/versions/` — versioned rule JSON seeds (C-3, canonical input to the rules engine)
- `scripts/` — psql setup, `api_smoke.py` (A-track live checks), `pg-local.ps1`
- `tests/` — cross-stack E2E (`e2e_flow.py`, hits the real backend :8000 + frontend :3000)

## Demo logins
| Role | Email | Password |
|---|---|---|
| Admin | `admin@mitra.in` | `admin@123` |
| Inspector | `inspector@mitra.in` | `inspector@123` |
| Reviewer | `reviewer@mitra.in` | `reviewer@123` |
| Auditor | `auditor@mitra.in` | `auditor@123` |

## Quick start (Windows, PowerShell)
```powershell
# backend
backend\.venv\Scripts\python.exe -m seed.seed            # once: users + rules
Start-Process backend\.venv\Scripts\uvicorn.exe -ArgumentList "app.main:app","--port","8000" -WorkingDirectory backend -WindowStyle Hidden

# frontend
cd frontend; npm run build; Start-Process npm -ArgumentList "run start -- -p 3000"
```

## Seed the demo dataset (PRD §41 Cases A–E)
```powershell
cd backend
.venv\Scripts\python.exe -m seed.demo_data --reset   # 5 deterministic cases, engine-computed outcomes
```

## Verifications
```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests -q     # 55 unit
backend\.venv\Scripts\python.exe scripts\api_smoke.py           # live A-track (backend :8000 up)
backend\.venv\Scripts\python.exe -m pytest tests/e2e_flow.py -v # cross-stack (backend + frontend up)
```

See `AGENTS.md` → Commands for full environment details (Postgres via `pg-local.ps1`, OCR smoke, pinned paddlepaddle 3.2.2). No Docker; Windows 11 + PowerShell environment.