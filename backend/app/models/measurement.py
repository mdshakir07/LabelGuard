from datetime import datetime, date
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    extracted_field_id: Mapped[int] = mapped_column(ForeignKey("extracted_fields.id"), nullable=False)
    image_id: Mapped[int] = mapped_column(ForeignKey("inspection_images.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)  # pixel_scale|font_size|placement|area
    value: Mapped[float] = mapped_column(nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Measurement kind={self.kind} value={self.value}{self.unit or ''}>"