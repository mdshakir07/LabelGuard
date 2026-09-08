from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(30), index=True, nullable=False)  # R-APP-01
    version: Mapped[str] = mapped_column(String(20), nullable=False)  # ruleset version e.g. PCR-2026.1
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="")
    source: Mapped[Optional[str]] = mapped_column(String(500))  # legal reference
    severity: Mapped[str] = mapped_column(String(20), default="mandatory")  # mandatory|advisory
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|published|superseded|retired
    effective_from: Mapped[Optional[str]] = mapped_column(String(20))
    effective_to: Mapped[Optional[str]] = mapped_column(String(20))
    rule_type: Mapped[str] = mapped_column(String(20), default="deterministic")  # deterministic|applicability|declaration
    params: Mapped[Optional[dict]] = mapped_column(JSON)
    applicability: Mapped[Optional[dict]] = mapped_column(JSON)
    condition: Mapped[Optional[str]] = mapped_column(String(1000))
    verify_prompt: Mapped[Optional[str]] = mapped_column(String(2000))  # human check guidance
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Rule id={self.rule_id} v={self.version} status={self.status}>"