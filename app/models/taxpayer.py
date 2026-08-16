"""Taxpayer registration (Sec. 4-5).

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


class Taxpayer(Base):
    __tablename__ = "taxpayer"

    taxpayer_id: Mapped[str] = pk()
    taxpayer_name: Mapped[str] = mapped_column(String(255), index=True)
    taxpayer_type: Mapped[str] = mapped_column(String(100))
    tax_identification_details: Mapped[str | None] = mapped_column(String(100), index=True)
    business_address: Mapped[str | None] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    mining_operations = relationship("MiningOperation", back_populates="taxpayer")
    shipments = relationship("Shipment", back_populates="taxpayer")
