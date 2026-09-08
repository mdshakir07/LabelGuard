"""B-OWNED service: preprocessing (deskew, denoise, perspective, contrast).

Takes raw image bytes, returns processed bytes. Never mutates the original.
The processed image is a derivation used for enhanced OCR.
"""
import numpy as np


def preprocess_image(image_bytes: bytes) -> bytes:
    try:
        import cv2
    except Exception:
        return image_bytes

    import numpy as np
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return image_bytes

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1) Remove noise via bilateral filter (preserves edges) or blur.
    gray = cv2.fastNlMeansDenoising(gray, h=8, templateWindowSize=7, searchWindowSize=21)

    # 2) Deskew: detect text angle via minAreaRect of non-zero threshold pixels.
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    coords = cv2.findNonZero(thresh)
    angle = 0.0
    if coords is not None:
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) > 0.5 and abs(angle) < 25:
            h, w = gray.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            gray = cv2.warpAffine(gray, M, (w, h),
                                  flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)

    # 3) Adaptive contrast to make text pop (CLAHE).
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 4) Sharpen lightly (unsharp mask) to improve OCR edges.
    blur = cv2.GaussianBlur(gray, (0, 0), 2.0)
    sharpened = cv2.addWeighted(gray, 1.6, blur, -0.6, 0)

    ok, buf = cv2.imencode(".png", sharpened)
    if not ok:
        return image_bytes
    return buf.tobytes()
