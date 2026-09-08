from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .inspection import Inspection
    from .ocr import OcrBlock
    from .assessment import Finding


class InspectionImage(Base):
    __tablename__ = "inspection_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("inspections.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(30), default="front")  # front|back|side|top|bottom|closeup|listing
    original_url: Mapped[str] = mapped_column(String(500), nullable=False)
    processed_url: Mapped[Optional[str]] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    quality_score_json: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="images")
    ocr_blocks = relationship("OcrBlock", back_populates="image", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="evidence_image")

    def __repr__(self) -> str:
        return f"<InspectionImage id={self.id} type={self.type} sha256={self.sha256[:8]}>"