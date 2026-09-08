from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .inspection import Inspection
    from .image import InspectionImage


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("inspections.id"), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    ruleset_version: Mapped[str] = mapped_column(String(40), nullable=False)  # snapshot
    result: Mapped[str] = mapped_column(String(30), nullable=False)  # PASS|POTENTIAL NON-COMPLIANCE|NEEDS VERIFICATION|NOT APPLICABLE
    evidence_json: Mapped[Optional[dict]] = mapped_column(JSON)  # links: image_ids, bboxes, ocr_ids, field_ids, confidence
    detail: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="assessments")
    findings: Mapped[List["Finding"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Assessment rule={self.rule_id} result={self.result}>"


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), nullable=False, index=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("inspections.id"), nullable=False, index=True)
    image_id: Mapped[Optional[int]] = mapped_column(ForeignKey("inspection_images.id"), index=True)
    ocr_block_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ocr_blocks.id"))
    rule_id: Mapped[str] = mapped_column(String(30), nullable=False)
    ruleset_version: Mapped[str] = mapped_column(String(40), nullable=False)
    bbox: Mapped[Optional[dict]] = mapped_column(JSON)
    summary: Mapped[str] = mapped_column(String(1000), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")  # info|warning|critical
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    automated_result: Mapped[str] = mapped_column(String(30), nullable=False)  # frozen snapshot of assessment.result
    review_status: Mapped[str] = mapped_column(String(30), default="pending")  # pending|CONFIRMED|REJECTED|MANUAL VERIFICATION
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    review_comment: Mapped[Optional[str]] = mapped_column(String(1000))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    assessment = relationship("Assessment", back_populates="findings")
    evidence_image = relationship("InspectionImage", back_populates="findings")

    def __repr__(self) -> str:
        return f"<Finding id={self.id} rule={self.rule_id} result={self.automated_result} review={self.review_status}>"