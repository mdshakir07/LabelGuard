# ml/ocr

OCR/CV work in progress (B-track). Pipeline entry points currently live in the backend services:

- `backend/app/services/ocr.py` — PaddleOCR recognition (`PP-OCRv6_medium_det/rec`, PaddlePaddle pinned to 3.2.2 for CPU)
- `backend/app/services/preprocessing.py` — image prep (dimension-preserving; stored width/height stay the OCR pixel space)
- `backend/app/services/quality.py` — Laplacian blur/brightness/contrast gate

This directory is reserved for standalone OCR model artifacts / experiment notebooks. Model files are cached in the user profile by `scripts/download_ocr_models.py` (see AGENTS.md); do not commit model weights (`.pdmodel`/`.pdiparams`) to the repo.