"""A-track end-to-end smoke (A1-A7 acceptance).

Usage: run with backend uvicorn already up on :8000.
    backend\\.venv\\Scripts\\python.exe scripts\\api_smoke.py
Exits non-zero on the first failing step.
"""
import io
import os
import sys
import tempfile
import time

import httpx
from PIL import Image, ImageDraw, ImageFont

BASE = os.environ.get("MM_BASE", "http://127.0.0.1:8000")


def make_label(path: str) -> None:
    img = Image.new("RGB", (900, 400), "white")
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 38)
    d.text((40, 70), "Net Wt. 500 g", fill="black", font=font)
    d.text((40, 160), "MRP (incl. of all taxes) Rs. 129.75", fill="black", font=font)
    d.text((40, 250), "Mfd. by Mitra Foods Pvt. Ltd., Mumbai", fill="black", font=font)
    img.save(path, "PNG")


def main() -> int:
    c = httpx.Client(base_url=BASE, timeout=120)
    checked = 0

    def ok(label: str) -> None:
        nonlocal checked
        checked += 1
        print(f"[{checked:02d}] OK  {label}")

    def fail(label: str, resp) -> None:
        print(f"[XX] FAIL {label}: HTTP {resp.status_code} {resp.text[:300]}")
        sys.exit(1)

    # 1 login
    r = c.post("/auth/login", json={"email": "inspector@mitra.in", "password": "inspector@123"})
    if r.status_code != 200 or "access_token" not in r.json():
        fail("login", r)
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    ok(f"login (user={r.json()['user']['role']})")

    # 1b bad login rejected
    r = c.post("/auth/login", json={"email": "inspector@mitra.in", "password": "wrong"})
    if r.status_code != 401:
        fail("bad login rejected", r)
    ok("bad login rejected (401)")

    # 1c no token -> 401
    r = c.get("/inspections")
    if r.status_code != 401:
        fail("no-token rejected", r)
    ok("no-token rejected (401)")


    # 1d auditor cannot create inspection
    r = c.post("/auth/login", json={"email": "auditor@mitra.in", "password": "auditor@123"})
    if r.status_code != 200:
        fail("auditor login", r)
    ah = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = c.post("/inspections", json={"location": "X"}, headers=ah)
    if r.status_code != 403:
        fail("auditor blocked from create", r)
    ok("RBAC: auditor blocked from create (403)")

    # 2 create inspection
    r = c.post("/inspections", headers=h,
               json={"location": "New Delhi", "channel": "retail",
                     "category": "food", "origin": "domestic"})
    if r.status_code != 201:
        fail("create inspection", r)
    insp = r.json()
    ok(f"inspection created {insp['public_id']} status={insp['status']}")

    # 2b duplicate public id not produced
    r2 = c.post("/inspections", headers=h, json={"location": "Mumbai"})
    if r2.status_code != 201 or r2.json()["public_id"] == insp["public_id"]:
        fail("public_id uniqueness", r2)
    ok(f"unique public_id ({insp['public_id']} != {r2.json()['public_id']})")

    # 3 upload image
    tmp = os.path.join(tempfile.gettempdir(), "mm_api_smoke.png")
    make_label(tmp)
    with open(tmp, "rb") as f:
        r = c.post(f"/inspections/{insp['id']}/images", headers=h,
                   data={"typ": "front"}, files={"files": ("label.png", f, "image/png")})
    if r.status_code != 201 or len(r.json()["created"]) != 1:
        fail("upload image", r)
    img = r.json()["created"][0]
    ok(f"image uploaded sha256={img['sha256'][:16]}... {img['width']}x{img['height']} "
       f"warnings={len(r.json()['warnings'])}")

    # 3b non-image rejected
    r = c.post(f"/inspections/{insp['id']}/images", headers=h,
               data={"typ": "front"},
               files={"files": ("bad.txt", b"not an image", "text/plain")})
    if r.status_code != 422:
        fail("non-image rejected", r)
    ok("non-image upload rejected (422)")

    # 4 process
    r = c.post(f"/inspections/{insp['id']}/process", headers=h)
    if r.status_code != 200:
        fail("start processing", r)
    ok("processing started (background)")
    detail = None
    for _ in range(80):
        time.sleep(3)
        det = c.get(f"/inspections/{insp['id']}", headers=h)
        if det.status_code != 200:
            fail("poll detail", det)
        detail = det.json()
        if detail["status"] in ("ready_for_review", "FAILED"):
            break
    if detail is None or detail["status"] != "ready_for_review":
        fail("processing to ready_for_review", det)
    ok(f"processing done -> ready_for_review (fields={len(detail['fields'])}, "
       f"assessments={len(detail['assessments'])})")
    if detail["process_error"]:
        fail("process_error non-null", det)

    # 4b re-run blocked
    r = c.post(f"/inspections/{insp['id']}/process", headers=h)
    if r.status_code != 409:
        fail("reprocess blocked", r)
    ok("reprocess blocked (409)")

    # 5 findings review (findings are nested under assessments; reviewer only)
    r = c.post("/auth/login", json={"email": "reviewer@mitra.in", "password": "reviewer@123"})
    if r.status_code != 200:
        fail("reviewer login", r)
    rh = {"Authorization": f"Bearer {r.json()['access_token']}"}
    findings = [f for a in detail.get("assessments", []) for f in a.get("findings", [])]
    review_target = None
    if findings:
        fid = findings[0]["id"]
        r = c.patch(f"/findings/{fid}", headers=rh,
                    json={"review_status": "CONFIRMED", "review_comment": "matches label"})
        if r.status_code != 200:
            fail("review finding", r)
        review_target = r.json()
        ok(f"finding {fid} reviewed -> {review_target['review_status']}")

        # 5b invalid state rejected
        r = c.patch(f"/findings/{fid}", headers=rh, json={"review_status": "LEGAL VIOLATION"})
        if r.status_code != 422:
            fail("invalid review state rejected", r)
        ok("invalid review state rejected (422)")

        # 5c inspector (not reviewer) review blocked
        r = c.patch(f"/findings/{fid}", headers=h, json={"review_status": "REJECTED"})
        if r.status_code != 403:
            fail("inspector review blocked", r)
        ok("inspector cannot review findings (403)")
    else:
        ok("no findings to review (skipped finding review checks)")

    # 6 rules + current ruleset (requires inspector or higher)
    r = c.get("/rules", headers=h)
    if r.status_code != 200 or r.json()["version"] != "PCR-2026.1":
        fail("list rules", r)
    ok(f"rules listed: version={r.json()['version']} count={len(r.json()['rules'])}")

    r = c.get("/rules/current", headers=h)
    if r.status_code != 200:
        fail("current ruleset", r)
    ok(f"current ruleset {r.json()['version']}")

    # 7 dashboard
    r = c.get("/dashboard", headers=h)
    if r.status_code != 200 or r.json()["total_inspections"] < 2:
        fail("dashboard", r)
    ok(f"dashboard total={r.json()['total_inspections']}")

    # 8 search
    r = c.get("/inspections", params={"q": "Delhi"}, headers=h)
    if r.status_code != 200 or not any(x["id"] == insp["id"] for x in r.json()["items"]):
        fail("search inspections", r)
    ok(f"search q=Delhi returns the inspection (total={r.json()['total']})")

    # 9 image serving
    r = c.get(f"/inspections/{insp['id']}/images/{img['id']}/file", headers=h)
    if r.status_code != 200 or len(r.content) < 1000:
        fail("serve image", r)
    ok(f"served image bytes={len(r.content)}")

    # 10b category confirmation (PRD §18 P0) on the second (draft) inspection
    rid = r2.json()["id"]
    r = c.get(f"/inspections/{rid}/category-suggestion", headers=h)
    if r.status_code != 200 or "suggestions" not in r.json():
        fail("category suggestion", r)
    ok(f"category suggestion shape (current={r.json()['current']!r})")
    r = c.patch(f"/inspections/{rid}/category", headers=h, json={"category": "beverages"})
    if r.status_code != 200 or r.json()["category"] != "beverages":
        fail("category confirm", r)
    ok("category confirmed via PATCH")

    # 11 inspection finalize flow (PRD §21): review then close
    r = c.post(f"/inspections/{insp['id']}/review", headers=h)
    if r.status_code != 403:
        fail("inspector cannot review inspection", r)
    ok("inspector cannot mark inspection reviewed (403)")

    r = c.post(f"/inspections/{insp['id']}/review", headers=rh)
    if r.status_code != 409:
        fail("review blocked by pending findings", r)
    ok("review blocked while findings pending (409)")

    pending = [f for a in detail.get("assessments", []) for f in a.get("findings", [])
               if f.get("review_status") == "pending"]
    for f in pending:
        fr = c.patch(f"/findings/{f['id']}", headers=rh,
                     json={"review_status": "CONFIRMED", "review_comment": "verified"})
        if fr.status_code not in (200, 422):
            fail("bulk confirm finding", fr)
    r = c.post(f"/inspections/{insp['id']}/review", headers=rh)
    if r.status_code != 200 or r.json()["status"] != "reviewed":
        fail("mark inspection reviewed", r)
    ok("inspection marked reviewed by reviewer")

    r = c.post(f"/inspections/{insp['id']}/close", headers=rh)
    if r.status_code != 200 or r.json()["status"] != "closed":
        fail("close inspection", r)
    ok(f"inspection closed (closed_at={r.json()['closed_at']})")

    r = c.post(f"/inspections/{insp['id']}/close", headers=rh)
    if r.status_code != 409:
        fail("double close rejected", r)
    ok("double-close rejected (409)")

    # 12 field edit locked after close
    fields = detail.get("fields", [])
    if fields:
        r = c.patch(f"/inspections/{insp['id']}/fields/{fields[0]['id']}", headers=h,
                    json={"raw": "override"})
        if r.status_code != 409:
            fail("field edit locked on closed", r)
        ok("field edit locked after close (409)")

    # 13 report generation (+ result)
    r = c.post(f"/inspections/{insp['id']}/report", headers=rh, json={"format": "pdf"})
    if r.status_code != 200:
        fail("generate report", r)
    ok("report generation started")
    rr = None
    for _ in range(10):
        time.sleep(1)
        rr = c.get(f"/inspections/{insp['id']}/report?fmt=pdf", headers=rh)
        if rr.status_code == 200:
            break
    if rr is None or rr.status_code != 200 or not rr.content.startswith(b"%PDF"):
        fail("report pdf fetch", rr)
    ok(f"report fetched ({len(rr.content)} bytes, PDF header OK)")

    c.close()
    print(f"\nALL {checked} A-TRACK SMOKE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())