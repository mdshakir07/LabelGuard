from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .image import InspectionImage


class OcrBlock(Base):
    __tablename__ = "ocr_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("inspection_images.id"), nullable=False, index=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("inspections.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, default=None)
    bbox: Mapped[dict] = mapped_column(JSON)  # {"x1":..,"y1":..,"x2":..,"y2":..} normalized or px
    source: Mapped[Optional[str]] = mapped_column(String(20))  # original|enhanced

    image = relationship("InspectionImage", back_populates="ocr_blocks")

    def __repr__(self) -> str:
        return f"<OcrBlock id={self.id} text={self.text[:30]!r} conf={self.confidence}>"