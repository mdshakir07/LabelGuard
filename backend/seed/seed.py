"""Standalone seeder: default users + ruleset load (C-3 seed JSON).

Usage (from backend/):
    .venv\\Scripts\\python.exe -m seed.seed            # users + rules
    .venv\\Scripts\\python.exe -m seed.seed --users-only
    .venv\\Scripts\\python.exe -m seed.seed --rules-only
Idempotent: skips existing users/rule versions.
"""
import argparse
import json
import sys
from pathlib import Path

from app.auth.security import hash_password
from app.db import SessionLocal
from app.models import Rule, User

DEFAULT_USERS = [
    {"name": "System Admin", "email": "admin@mitra.in", "role": "admin", "password": "admin@123"},
    {"name": "Field Inspector", "email": "inspector@mitra.in", "role": "inspector", "password": "inspector@123"},
    {"name": "Review Officer", "email": "reviewer@mitra.in", "role": "reviewer", "password": "reviewer@123"},
    {"name": "Audit Observer", "email": "auditor@mitra.in", "role": "auditor", "password": "auditor@123"},
]

RULES_FILE = Path(__file__).resolve().parents[2] / "rules" / "versions" / "seed_rules_v1.json"


def seed_users(db) -> None:
    for u in DEFAULT_USERS:
        if db.query(User).filter(User.email == u["email"]).first():
            continue
        db.add(User(
            name=u["name"], email=u["email"], role=u["role"],
            password_hash=hash_password(u["password"]), status="active",
        ))
    db.commit()


def seed_rules(db) -> None:
    if not RULES_FILE.exists():
        print(f"[warn] rules file not found: {RULES_FILE}")
        return
    data = json.loads(RULES_FILE.read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    added = 0
    default_status = data.get("ruleset", {}).get("review_status", "draft")
    for r in rules:
        exists = db.query(Rule).filter(
            Rule.rule_id == r["rule_id"], Rule.version == r.get("version", data.get("version")),
        ).first()
        if exists:
            continue
        db.add(Rule(
            rule_id=r["rule_id"],
            version=r.get("version", data.get("version", "PCR-2026.1")),
            title=r.get("title", ""),
            description=r.get("description", ""),
            source=r.get("source"),
            severity=r.get("severity", "mandatory"),
            status=r.get("status", default_status),
            effective_from=r.get("effective_from"),
            effective_to=r.get("effective_to"),
            rule_type=r.get("rule_type", "deterministic"),
            params=r.get("params"),
            applicability=r.get("applicability"),
            condition=r.get("condition"),
            verify_prompt=r.get("verify_prompt"),
        ))
        added += 1
    db.commit()
    print(f"rules: added {added} new / total {db.query(Rule).count()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--users-only", action="store_true")
    parser.add_argument("--rules-only", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if not args.rules_only:
            seed_users(db)
            print(f"users: total {db.query(User).count()}")
        if not args.users_only:
            seed_rules(db)
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())