# ml/detectors

Reserved for detector-model work (P1: calibrated font-size measurement, barcode/GTIN, sticker detection for R-DECL-11). Not in MVP P0 scope — see PRD §40.

Current evidence model: OCR boxes are stored in absolute pixels and reused as findings bboxes (see `backend/app/models/ocr.py`, `services/evidence.py`).