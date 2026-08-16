"""Taxpayer's remedies: protest, refund, credit (Sec. 13).

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


class RemedyType(Base):
    __tablename__ = "remedy_type"

    remedy_type_id: Mapped[str] = pk()
    remedy_name: Mapped[str] = mapped_column(String(50), unique=True)  # Protest | Refund | Credit
    filing_deadline: Mapped[str | None] = mapped_column(String(150))


class TaxpayerRemedy(Base):
    __tablename__ = "taxpayer_remedy"

    remedy_id: Mapped[str] = pk()
    taxpayer_id: Mapped[str] = fk("taxpayer.taxpayer_id")
    assessment_id: Mapped[str | None] = fk("tax_assessment.assessment_id", nullable=True)
    remedy_type_id: Mapped[str] = fk("remedy_type.remedy_type_id")
    filing_date: Mapped[dt.date] = mapped_column(Date, index=True)
    decision_date: Mapped[dt.date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="filed", index=True)

    remedy_type = relationship("RemedyType")
