import tempfile
import os
from PIL import Image, ImageDraw, ImageFont

from paddleocr import PaddleOCR

tmp = tempfile.gettempdir()
img_path = os.path.join(tmp, "mm_ocr_smoke.png")

img = Image.new("RGB", (900, 400), "white")
d = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 40)
except OSError:
    font = ImageFont.load_default()
d.text((40, 60), "Net Wt. 500 g", fill="black", font=font)
d.text((40, 160), "MRP (incl. of all taxes) Rs. 129.75", fill="black", font=font)
d.text((40, 260), "Mfd. by Mitra Foods Pvt. Ltd., Mumbai", fill="black", font=font)
img.save(img_path)

ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, lang="en")
result = ocr.predict(img_path)

print("=== SMOKE OCR RESULT ===")
res = result[0] if isinstance(result, (list, tuple)) else result
for line in res["rec_texts"]:
    print(line)
print("=== DONE ===")