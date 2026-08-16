"""Tax assessment and payment (Sec. 7, 8, 14).

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


class TaxAssessment(Base):
    __tablename__ = "tax_assessment"

    assessment_id: Mapped[str] = pk()
    taxpayer_id: Mapped[str] = fk("taxpayer.taxpayer_id")
    shipment_id: Mapped[str] = fk("shipment.shipment_id")
    estimated_gross_receipts: Mapped[float | None] = mapped_column(Money)
    gross_receipts: Mapped[float | None] = mapped_column(Money)
    tax_rate: Mapped[float] = mapped_column(Rate, default=0.01)
    tax_due: Mapped[float] = mapped_column(Money, default=0)
    surcharge: Mapped[float] = mapped_column(Money, default=0)
    interest: Mapped[float] = mapped_column(Money, default=0)
    assessment_stage: Mapped[str] = mapped_column(String(20), index=True)  # provisional | final | reassessment
    assessment_date: Mapped[dt.date] = mapped_column(Date, index=True)

    shipment = relationship("Shipment", back_populates="assessments")
    payments = relationship("TaxPayment", back_populates="assessment")


class TaxPayment(Base):
    __tablename__ = "tax_payment"

    payment_id: Mapped[str] = pk()
    taxpayer_id: Mapped[str] = fk("taxpayer.taxpayer_id")
    assessment_id: Mapped[str] = fk("tax_assessment.assessment_id")
    clearance_id: Mapped[str | None] = fk(
        "provincial_soil_depletion_tax_clearance.clearance_id", nullable=True
    )
    payment_date: Mapped[dt.date] = mapped_column(Date, index=True)
    amount_paid: Mapped[float] = mapped_column(Money)
    payment_type: Mapped[str] = mapped_column(String(30), index=True)  # provisional | final | penalty

    assessment = relationship("TaxAssessment", back_populates="payments")
    clearance = relationship("ProvincialSoilDepletionTaxClearance", back_populates="payments")
