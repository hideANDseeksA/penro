"""Quarterly soil depletion tax return (Sec. 8d).

Entity and field names are taken verbatim from
`camarines_norte_soil_depletion_tax_erd_full.md`.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.types import GUID, Money, Rate, Volume
from app.core.columns import fk, pk


class SoilDepletionTaxReturn(Base):
    __tablename__ = "soil_depletion_tax_return"

    return_id: Mapped[str] = pk()
    taxpayer_id: Mapped[str] = fk("taxpayer.taxpayer_id")
    return_period: Mapped[str] = mapped_column(String(10), index=True)  # e.g. 2026Q1
    filing_date: Mapped[dt.date | None] = mapped_column(Date, index=True)
    reported_gross_receipts: Mapped[float | None] = mapped_column(Money)
    return_status: Mapped[str] = mapped_column(String(30), default="draft", index=True)

    return_shipments = relationship("ReturnShipment", back_populates="tax_return")

    __table_args__ = (Index("ix_return_taxpayer_period", "taxpayer_id", "return_period", unique=True),)


class ReturnShipment(Base):
    __tablename__ = "return_shipment"

    return_shipment_id: Mapped[str] = pk()
    return_id: Mapped[str] = fk("soil_depletion_tax_return.return_id")
    shipment_id: Mapped[str] = fk("shipment.shipment_id")
    reported_volume_shipped: Mapped[float | None] = mapped_column(Volume)
    otp_reference: Mapped[str | None] = mapped_column(String(100), index=True)

    tax_return = relationship("SoilDepletionTaxReturn", back_populates="return_shipments")
