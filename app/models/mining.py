"""Mining operations, permits, sites, minerals and extraction records (Sec. 4-5, Sec. 10).

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


mining_operation_extraction_site = Table(
    "mining_operation_extraction_site",
    Base.metadata,
    Column("mining_operation_id", GUID(), ForeignKey("mining_operation.mining_operation_id"), primary_key=True),
    Column("extraction_site_id", GUID(), ForeignKey("extraction_site.extraction_site_id"), primary_key=True),
)

mining_operation_mineral = Table(
    "mining_operation_mineral",
    Base.metadata,
    Column("mining_operation_id", GUID(), ForeignKey("mining_operation.mining_operation_id"), primary_key=True),
    Column("mineral_id", GUID(), ForeignKey("mineral.mineral_id"), primary_key=True),
)


class MiningOperationType(Base):
    __tablename__ = "mining_operation_type"

    operation_type_id: Mapped[str] = pk()
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))


class MiningOperation(Base):
    __tablename__ = "mining_operation"

    mining_operation_id: Mapped[str] = pk()
    taxpayer_id: Mapped[str] = fk("taxpayer.taxpayer_id")
    operation_type_id: Mapped[str] = fk("mining_operation_type.operation_type_id")
    operation_name: Mapped[str] = mapped_column(String(255), index=True)
    legal_basis: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)

    taxpayer = relationship("Taxpayer", back_populates="mining_operations")
    operation_type = relationship("MiningOperationType")
    permit_authorities = relationship("PermitAuthority", back_populates="mining_operation")
    extraction_sites = relationship("ExtractionSite", secondary=mining_operation_extraction_site)
    minerals = relationship("Mineral", secondary=mining_operation_mineral)


class PermitAuthority(Base):
    __tablename__ = "permit_authority"

    permit_authority_id: Mapped[str] = pk()
    mining_operation_id: Mapped[str] = fk("mining_operation.mining_operation_id")
    permit_type: Mapped[str] = mapped_column(String(100), index=True)
    permit_number: Mapped[str] = mapped_column(String(100), index=True)
    issuing_authority: Mapped[str | None] = mapped_column(String(150))
    issue_date: Mapped[dt.date | None] = mapped_column(Date)
    expiry_date: Mapped[dt.date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), default="valid")

    mining_operation = relationship("MiningOperation", back_populates="permit_authorities")


class ExtractionSite(Base):
    __tablename__ = "extraction_site"

    extraction_site_id: Mapped[str] = pk()
    site_name: Mapped[str] = mapped_column(String(255), index=True)
    municipality: Mapped[str | None] = mapped_column(String(100), index=True)
    barangay: Mapped[str | None] = mapped_column(String(100))
    coordinates: Mapped[str | None] = mapped_column(String(100))


class Mineral(Base):
    __tablename__ = "mineral"

    mineral_id: Mapped[str] = pk()
    mineral_name: Mapped[str] = mapped_column(String(150), index=True)
    mineral_category: Mapped[str] = mapped_column(String(100), index=True)
    ordinary_quarry_resource_excluded: Mapped[bool] = mapped_column(Boolean, default=False)


class ExtractionRecord(Base):
    __tablename__ = "extraction_record"

    extraction_record_id: Mapped[str] = pk()
    extraction_site_id: Mapped[str] = fk("extraction_site.extraction_site_id")
    mineral_id: Mapped[str] = fk("mineral.mineral_id")
    extraction_date: Mapped[dt.date] = mapped_column(Date, index=True)
    volume_extracted: Mapped[float] = mapped_column(Volume)
    grade: Mapped[str | None] = mapped_column(String(100))
    quality: Mapped[str | None] = mapped_column(String(100))
