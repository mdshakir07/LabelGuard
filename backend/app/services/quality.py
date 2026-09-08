"""B-OWNED service: quality gate (replaces placeholder).

Scores image quality via Laplacian variance (blur), brightness, contrast,
and glare detection (overexposed highlights). Returns 0..1 score + warnings.
Contract: analyze_image(image_bytes) -> {
    "score": float, "warnings": [str], "recommendation": str
}
"""
import numpy as np


def analyze_image(image_bytes: bytes) -> dict:
    try:
        import cv2
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return {"score": 0.5, "warnings": ["could not inspect"], "recommendation": "proceed"}
    if img is None:
        return {"score": 0.5, "warnings": ["could not decode"], "recommendation": "proceed"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    warnings = []

    # --- Sharpness via Laplacian variance ---
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    if variance < 25:
        clarity, warnings = 0.3, ["blur detected - retake"]
    elif variance < 60:
        clarity, warnings = 0.6, ["low clarity"]
    else:
        clarity = 0.95

    # --- Brightness ---
    mean_brightness = gray.mean()
    if mean_brightness < 40:
        brightness = 0.1
        warnings.append("too dark - improve lighting")
    elif mean_brightness < 80:
        brightness = 0.5
        warnings.append("under-exposed")
    elif mean_brightness > 235:
        brightness = 0.2
        warnings.append("over-exposed / glare")
    else:
        brightness = 0.9

    # --- Contrast (std dev) - low contrast makes OCR hard ---
    contrast = float(gray.std())
    if contrast < 25:
        warnings.append("low contrast")

    # --- Resolution ---
    resolution_ok = img.shape[0] >= 480 and img.shape[1] >= 480
    if not resolution_ok:
        warnings.append("low resolution")

    score = round(0.5 * clarity + 0.3 * brightness + 0.2 * min(contrast / 60, 1.0), 3)
    score = max(0.0, min(1.0, score))
    if score < 0.4:
        recommendation = "retake recommended"
    elif score < 0.65:
        recommendation = "proceed with caution"
    else:
        recommendation = "proceed"

    return {"score": score, "warnings": warnings, "recommendation": recommendation}