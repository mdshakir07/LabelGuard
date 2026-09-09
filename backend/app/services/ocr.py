"""B-OWNED service: PaddleOCR wrapper (basic pass already verified).

Owner B expands with enhance-and-rerun + overlap merge.
Contract: recognize(path|bytes) -> list[{"text", "confidence", "bbox", "source"}]
"""
from functools import lru_cache


@lru_cache(maxsize=1)
def _predictor():
    from paddleocr import PaddleOCR

    return PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        lang="en",
    )


def recognize(image_bytes: bytes, source: str = "original") -> list:
    import numpy as np
    from PIL import Image

    with Image.open(__import__("io").BytesIO(image_bytes)) as im:
        arr = np.asarray(im.convert("RGB"))

    predictor = _predictor()
    result = predictor.predict(arr)
    blocks = []
    for page in result:
        rec = page.get("rec_texts") or []
        scores = page.get("rec_scores") or []
        polys = page.get("rec_polys") or []
        for text, score, poly in zip(rec, scores, polys):
            if not text or not text.strip():
                continue
            pts = [[float(p[0]), float(p[1])] for p in poly]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            blocks.append({
                "text": str(text).strip(),
                "confidence": round(float(score), 4) if score is not None else None,
                "bbox": {"x1": min(xs), "y1": min(ys), "x2": max(xs), "y2": max(ys)},
                "source": source,
            })
    return blocks