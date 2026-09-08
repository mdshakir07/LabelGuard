from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .inspection import Inspection


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inspection_id: Mapped[int] = mapped_column(ForeignKey("inspections.id"), nullable=False, index=True)
    field: Mapped[str] = mapped_column(String(40), nullable=False)  # C-4 field name (mrp, net_qty, unit_sale_price, ...)
    raw: Mapped[Optional[str]] = mapped_column(String(500))
    normalized: Mapped[Optional[dict]] = mapped_column(JSON)  # canonical value; PRD §24: never silently overwrite raw
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    source_ocr_ids: Mapped[Optional[list]] = mapped_column(JSON)  # ocr_block ids used
    is_edited: Mapped[bool] = mapped_column(default=False)
    edited_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    inspection = relationship("Inspection", back_populates="fields")

    def __repr__(self) -> str:
        return f"<ExtractedField id={self.id} field={self.field} raw={self.raw!r}>"