"""One-time PaddleOCR model download + smoke check (Phase 0 / B-track bootstrap).

Generates a synthetic label image, runs OCR, prints detected text + confidence.
Model files are cached by PaddleOCR in the user profile (~/.paddleocr) on first run.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def make_test_label(out: Path) -> str:
    img = Image.new("RGB", (1200, 300), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 42)
    except Exception:
        font = ImageFont.load_default()
    d.text((60, 40), "Net Weight 500 g", fill="black", font=font)
    d.text((60, 130), "MRP Rs. 129.75 (incl. of all taxes)", fill="black", font=font)
    d.text((60, 220), "Mfd: 2026-08  Packed By: SS Foods", fill="black", font=font)
    img.save(out)
    return str(out)


def main() -> None:
    out = Path("backend/storage") / "_paddle_smoke.png"
    path = make_test_label(out)

    from paddleocr import PaddleOCR

    ocr = PaddleOCR(lang="en", use_doc_orientation_classify=False, use_doc_unwarping=False)
    result = ocr.predict(path)
    print("--- OCR results ---")
    n = 0
    for res in result:
        for item in res["rec_texts"]:
            n += 1
    print(f"{n} text lines detected on smoke image.")
    out.unlink(missing_ok=True)
    print("PaddleOCR models downloaded and verified.")


if __name__ == "__main__":
    main()