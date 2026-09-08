from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth.deps import require_roles, require_or_higher
from ..db import get_db
from ..models import Inspection, Rule, User
from ..schemas.rule import (RuleCreate, RuleFlowOut, RuleListOut,
                            RulePublishIn)
from ..services.audit import log_audit

router = APIRouter(prefix="/rules", tags=["rules"])

# B owns rule JSON; A owns repo integration. Drafts visible to inspec-browsers,
# creation/publish restricted to admin. Inspections snapshot the version used.


@router.get("", response_model=RuleListOut)
def list_rules(
    version: Optional[str] = None,
    status_filter: Optional[str] = "published",
    user: User = Depends(require_or_higher("inspector")),
    db: Session = Depends(get_db),
):
    query = db.query(Rule)
    if version:
        query = query.filter(Rule.version == version)
    elif status_filter:
        query = query.filter(Rule.status == status_filter)
    rows = query.order_by(Rule.rule_id).all()
    active_version = version or (rows[0].version if rows else "PCR-2026.1")
    return RuleListOut(version=active_version, rules=[RuleFlowOut.model_validate(r) for r in rows])


@router.post("", response_model=RuleFlowOut, status_code=status.HTTP_201_CREATED)
def create_rule(
    body: RuleCreate,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    rule = Rule(**body.model_dump())
    db.add(rule)
    db.flush()
    log_audit(db, "rule_create", "rule", entity_id=body.rule_id, actor=admin,
              after={"version": rule.version, "status": rule.status})
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/{rule_id}/publish", response_model=RuleFlowOut)
def publish_rule(
    rule_id: int,
    body: RulePublishIn,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    rule = db.get(Rule, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    before = {"status": rule.status}
    rule.status = body.status
    log_audit(db, "rule_publish", "rule", entity_id=rule.rule_id, actor=admin,
              before=before, after={"status": body.status})
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/current")
def current_ruleset(
    user: User = Depends(require_or_higher("inspector")),
    db: Session = Depends(get_db),
):
    latest = (
        db.query(Rule.version)
        .filter(Rule.status == "published")
        .order_by(Rule.effective_from.desc())
        .first()
    )
    version = latest[0] if latest else "PCR-2026.1"
    count = db.query(Rule).filter(Rule.version == version, Rule.status == "published").count()
    return {"version": version, "published_rule_count": count}