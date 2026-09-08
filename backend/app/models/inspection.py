from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .image import InspectionImage
    from .field import ExtractedField
    from .assessment import Assessment


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_id: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)  # MM-YYYY-NNNN
    inspector_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    location: Mapped[str] = mapped_column(String(255), default="")
    channel: Mapped[str] = mapped_column(String(30), default="retail")  # retail|ecommerce|institutional|industrial
    inspection_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    category: Mapped[Optional[str]] = mapped_column(String(80), index=True)
    package_structure: Mapped[str] = mapped_column(String(30), default="single")  # single|multi_product|multi_unit|promotional
    origin: Mapped[str] = mapped_column(String(20), default="domestic")  # domestic|imported
    special_status: Mapped[Optional[str]] = mapped_column(String(40))
    product_name_hint: Mapped[Optional[str]] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(String(30), default="draft",
                                        index=True)  # draft|processing|ready_for_review|reviewed|closed
    ruleset_version: Mapped[Optional[str]] = mapped_column(String(40))
    process_error: Mapped[Optional[str]] = mapped_column(String(1000))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    inspector = relationship("User", foreign_keys=[inspector_id])
    images: Mapped[List["InspectionImage"]] = relationship(
        back_populates="inspection", cascade="all, delete-orphan")
    fields: Mapped[List["ExtractedField"]] = relationship(
        back_populates="inspection", cascade="all, delete-orphan")
    assessments: Mapped[List["Assessment"]] = relationship(
        back_populates="inspection", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Inspection id={self.id} public_id={self.public_id} status={self.status}>"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    brand: Mapped[Optional[str]] = mapped_column(String(255))
    category: Mapped[Optional[str]] = mapped_column(String(80))
    manufacturer: Mapped[Optional[str]] = mapped_column(String(255))
    origin: Mapped[Optional[str]] = mapped_column(String(80))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name}>"