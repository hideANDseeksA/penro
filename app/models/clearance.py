"""Provincial Soil Depletion Tax Clearance (Sec. 8-9).

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


class ProvincialSoilDepletionTaxClearance(Base):
    __tablename__ = "provincial_soil_depletion_tax_clearance"

    clearance_id: Mapped[str] = pk()
    taxpayer_id: Mapped[str] = fk("taxpayer.taxpayer_id")
    shipment_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("shipment.shipment_id"), unique=True, index=True
    )
    application_date: Mapped[dt.date] = mapped_column(Date, index=True)
    issuance_date: Mapped[dt.date | None] = mapped_column(Date)
    clearance_status: Mapped[str] = mapped_column(String(50), default="applied", index=True)

    shipment = relationship("Shipment", back_populates="clearance")
    payments = relationship("TaxPayment", back_populates="clearance")
