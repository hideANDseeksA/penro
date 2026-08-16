"""Shipments and their supporting documents (Sec. 6-8).

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


class Shipment(Base):
    __tablename__ = "shipment"

    shipment_id: Mapped[str] = pk()
    taxpayer_id: Mapped[str] = fk("taxpayer.taxpayer_id")
    mining_operation_id: Mapped[str] = fk("mining_operation.mining_operation_id")
    extraction_site_id: Mapped[str] = fk("extraction_site.extraction_site_id")
    mineral_id: Mapped[str] = fk("mineral.mineral_id")
    shipment_date: Mapped[dt.date] = mapped_column(Date, index=True)
    estimated_volume: Mapped[float | None] = mapped_column(Volume)
    final_volume: Mapped[float | None] = mapped_column(Volume)
    gross_receipts: Mapped[float | None] = mapped_column(Money)
    buyer: Mapped[str | None] = mapped_column(String(255), index=True)
    destination: Mapped[str | None] = mapped_column(String(255))
    shipment_status: Mapped[str] = mapped_column(String(50), default="declared", index=True)

    taxpayer = relationship("Taxpayer", back_populates="shipments")
    documents = relationship("ShipmentDocument", back_populates="shipment")
    assessments = relationship("TaxAssessment", back_populates="shipment")
    clearance = relationship("ProvincialSoilDepletionTaxClearance", back_populates="shipment", uselist=False)

    __table_args__ = (Index("ix_shipment_taxpayer_date", "taxpayer_id", "shipment_date"),)


class DocumentType(Base):
    __tablename__ = "document_type"

    document_type_id: Mapped[str] = pk()
    document_name: Mapped[str] = mapped_column(String(255))
    mineral_scope: Mapped[str] = mapped_column(String(50), index=True)  # iron_ore | gold | other
    stage: Mapped[str] = mapped_column(String(20), index=True)          # provisional | final


class ShipmentDocument(Base):
    __tablename__ = "shipment_document"

    shipment_document_id: Mapped[str] = pk()
    shipment_id: Mapped[str] = fk("shipment.shipment_id")
    document_type_id: Mapped[str] = fk("document_type.document_type_id")
    document_number: Mapped[str | None] = mapped_column(String(100))
    document_date: Mapped[dt.date | None] = mapped_column(Date)
    document_status: Mapped[str] = mapped_column(String(50), default="submitted", index=True)

    shipment = relationship("Shipment", back_populates="documents")
    document_type = relationship("DocumentType")
