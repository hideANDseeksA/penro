"""Violations and sanctions (Sec. 15).

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


class Violation(Base):
    __tablename__ = "violation"

    violation_id: Mapped[str] = pk()
    taxpayer_id: Mapped[str] = fk("taxpayer.taxpayer_id")
    shipment_id: Mapped[str | None] = fk("shipment.shipment_id", nullable=True)
    return_id: Mapped[str | None] = fk("soil_depletion_tax_return.return_id", nullable=True)
    violation_date: Mapped[dt.date] = mapped_column(Date, index=True)
    violation_type: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)

    sanctions = relationship("PenaltyOrAdministrativeSanction", back_populates="violation")


class PenaltyOrAdministrativeSanction(Base):
    __tablename__ = "penalty_or_administrative_sanction"

    sanction_id: Mapped[str] = pk()
    violation_id: Mapped[str] = fk("violation.violation_id")
    sanction_type: Mapped[str] = mapped_column(String(50), index=True)  # fine | suspension | revocation | referral
    fine_amount: Mapped[float | None] = mapped_column(Money)
    sanction_date: Mapped[dt.date] = mapped_column(Date, index=True)
    settled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    violation = relationship("Violation", back_populates="sanctions")
