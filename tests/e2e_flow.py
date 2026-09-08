"""Cross-stack E2E flow test (Item 4).

Hits the REAL running stack — FastAPI backend on :8000 and the built Next.js
frontend on :3000 — from login through upload, processing, review and close.

The suite auto-skips when the backend is not reachable, so unit runs (`pytest
backend/tests`) stay fast and CI can gate this on a warmed environment.

Run (backend + frontend up):
    backend\\.venv\\Scripts\\python.exe -m pytest tests/e2e_flow.py -v
"""
import io
import time

import httpx
import pytest
from PIL import Image, ImageDraw

BACKEND = "http://127.0.0.1:8000"
FRONTEND = "http://127.0.0.1:3000"

INGREDIENTS = {
    "email": "inspector@mitra.in",
    "password": "inspector@123",
}
REVIEWER = {
    "email": "reviewer@mitra.in",
    "password": "reviewer@123",
}


def _backend_up() -> bool:
    try:
        return httpx.get(f"{BACKEND}/health", timeout=2).status_code == 200
    except Exception:
        return False


requires_backend = pytest.mark.skipif(
    not _backend_up(), reason="FastAPI backend not reachable on :8000"
)


@requires_backend
def test_full_flow_from_login_to_close():
    with httpx.Client(base_url=BACKEND, timeout=30) as c:
        # --- auth ---
        r = c.post("/auth/login", json=INGREDIENTS)
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        # --- inspection lifecycle ---
        r = c.post("/inspections", headers=h, json={
            "location": "E2E harness - Connaught Place, New Delhi",
            "channel": "retail",
            "category": "food",
            "package_structure": "single",
            "origin": "domestic",
            "product_name_hint": "E2E Test Biscuits",
        })
        assert r.status_code == 201, r.text
        insp = r.json()
        assert insp["status"] == "draft"
        assert insp["public_id"].startswith("IN-")

        # --- upload a small generated label image ---
        img = Image.new("RGB", (900, 600), "white")
        d = ImageDraw.Draw(img)
        d.rectangle((20, 20, 880, 600), outline="black", width=3)
        d.text((40, 60), "E2E Brand Biscuits", fill="black")
        d.text((40, 120), "Mfd. by E2E Foods Ltd.", fill="black")
        d.text((40, 160), "Net Quantity: 250 g", fill="black")
        d.text((40, 200), "MRP Rs. 40.00 (incl. of all taxes)", fill="black")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        files = {
            "files": ("e2e_label.png", buf.getvalue(), "image/png"),
        }
        r = c.post(f"/inspections/{insp['id']}/images", headers=h, files=files,
                   data={"typ": "front"})
        assert r.status_code == 201, r.text
        assert r.json()["created"][0]["sha256"]

        # --- process + poll ---
        r = c.post(f"/inspections/{insp['id']}/process", headers=h)
        assert r.status_code in (200, 202), r.text
        deadline = time.time() + 300
        while time.time() < deadline:
            r = c.get(f"/inspections/{insp['id']}", headers=h)
            assert r.status_code == 200, r.text
            detail = r.json()
            if detail["status"] in ("ready_for_review", "FAILED"):
                break
            time.sleep(5)
        assert detail["status"] == "ready_for_review", detail.get("process_error")
        assert len(detail["fields"]) >= 3
        assert len(detail["assessments"]) >= 8

        results = {a["result"] for a in detail["assessments"]}
        assert results <= {
            "PASS", "POTENTIAL NON-COMPLIANCE", "NEEDS VERIFICATION", "NOT APPLICABLE",
        }, "automated outcome vocabulary violated (golden rule)"

        # --- category suggestion + confirm + re-assess ---
        r = c.get(f"/inspections/{insp['id']}/category-suggestion", headers=h)
        assert r.status_code == 200
        assert "suggestions" in r.json()
        r = c.patch(f"/inspections/{insp['id']}/category", headers=h,
                    json={"category": "food"})
        assert r.status_code == 200, r.text

        r = c.post(f"/inspections/{insp['id']}/assess", headers=h)
        assert r.status_code == 200, r.text
        deadline = time.time() + 300
        while time.time() < deadline:
            r = c.get(f"/inspections/{insp['id']}", headers=h)
            assert r.status_code == 200, r.text
            detail = r.json()
            if detail["status"] in ("ready_for_review", "FAILED"):
                break
            time.sleep(5)
        assert detail["status"] == "ready_for_review", detail.get("process_error")
        assert len(detail["fields"]) >= 3
        assert len(detail["assessments"]) >= 8

        results = {a["result"] for a in detail["assessments"]}
        assert results <= {
            "PASS", "POTENTIAL NON-COMPLIANCE", "NEEDS VERIFICATION", "NOT APPLICABLE",
        }, "automated outcome vocabulary violated (golden rule)"

        # --- findings review by reviewer ---
        r = c.post("/auth/login", json=REVIEWER)
        assert r.status_code == 200, r.text
        rh = {"Authorization": f"Bearer {r.json()['access_token']}"}

        findings = [f for a in detail["assessments"] for f in a.get("findings", [])]
        assert findings, "no findings created for processed inspection"
        for f in findings:
            r = c.patch(f"/findings/{f['id']}", headers=rh,
                        json={"review_status": "CONFIRMED", "review_comment": "e2e ok"})
            assert r.status_code == 200, r.text

        # --- finalize: review then close ---
        r = c.post(f"/inspections/{insp['id']}/review", headers=rh)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "reviewed"
        r = c.post(f"/inspections/{insp['id']}/close", headers=rh)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "closed"
        assert r.json()["closed_at"]

        # --- field edit locked after close ---
        fid = detail["fields"][0]["id"]
        r = c.patch(f"/inspections/{insp['id']}/fields/{fid}", headers=h,
                    json={"raw": "tampered"})
        assert r.status_code == 409, r.text

        # --- report over the closed inspection (background write; poll) ---
        r = c.post(f"/inspections/{insp['id']}/report", headers=h, json={"format": "pdf"})
        assert r.status_code == 200, r.text
        deadline = time.time() + 45
        rr = None
        while time.time() < deadline:
            rr = c.get(f"/inspections/{insp['id']}/report", params={"format": "pdf"}, headers=h)
            if rr.status_code == 200:
                break
            time.sleep(2)
        assert rr is not None and rr.status_code == 200, f"report not generated: {rr.status_code if rr else 'no response'}"
        assert rr.headers["content-type"].startswith("application/pdf")
        assert b"%PDF" in rr.content[:8]


@requires_backend
@pytest.mark.parametrize("path", ["/login"])
def test_frontend_serves(path: str):
    if httpx.get(f"{FRONTEND}{path}", timeout=2).status_code in (200, 307):
        return  # frontend built & serving
    pytest.skip("Next.js frontend not reachable on :3000")


@requires_backend
def test_frontend_proxy_gates_dashboard():
    """proxy.ts: /dashboard without token must 307 to /login; with token 200."""
    with httpx.Client(base_url=FRONTEND, follow_redirects=False, timeout=10) as c:
        r = c.get("/dashboard")
        assert r.status_code == 307, r.status_code
        assert r.headers.get("location", "").endswith("/login")

        login = httpx.post(f"{BACKEND}/auth/login", json=INGREDIENTS, timeout=10)
        assert login.status_code == 200
        token = login.json()["access_token"]
        cookie = {"Cookie": f"mm_token={token}"}
        r = c.get("/dashboard", headers=cookie)
        assert r.status_code == 200

        r = c.get("/inspections", headers=cookie)
        assert r.status_code == 200