"""Provincial monitoring, examination of books and reporting (Sec. 10-12).

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


class ProvincialOffice(Base):
    __tablename__ = "provincial_office"

    provincial_office_id: Mapped[str] = pk()
    office_name: Mapped[str] = mapped_column(String(150), unique=True)
    office_role: Mapped[str | None] = mapped_column(String(255))


class ProvincialMonitoringRecord(Base):
    __tablename__ = "provincial_monitoring_record"

    monitoring_record_id: Mapped[str] = pk()
    mining_operation_id: Mapped[str | None] = fk("mining_operation.mining_operation_id", nullable=True)
    shipment_id: Mapped[str | None] = fk("shipment.shipment_id", nullable=True)
    provincial_office_id: Mapped[str] = fk("provincial_office.provincial_office_id")
    monitoring_date: Mapped[dt.date] = mapped_column(Date, index=True)
    volume: Mapped[float | None] = mapped_column(Volume)
    findings: Mapped[str | None] = mapped_column(Text)


class NationalAgency(Base):
    __tablename__ = "national_agency"

    national_agency_id: Mapped[str] = pk()
    agency_name: Mapped[str] = mapped_column(String(150), unique=True)


class NationalAgencyDocument(Base):
    __tablename__ = "national_agency_document"

    national_agency_document_id: Mapped[str] = pk()
    shipment_id: Mapped[str] = fk("shipment.shipment_id")
    national_agency_id: Mapped[str] = fk("national_agency.national_agency_id")
    document_name: Mapped[str] = mapped_column(String(255))
    document_date: Mapped[dt.date | None] = mapped_column(Date)


class BooksExaminationRecord(Base):
    __tablename__ = "books_examination_record"

    examination_id: Mapped[str] = pk()
    taxpayer_id: Mapped[str] = fk("taxpayer.taxpayer_id")
    provincial_office_id: Mapped[str] = fk("provincial_office.provincial_office_id")
    examination_date: Mapped[dt.date] = mapped_column(Date, index=True)
    scope: Mapped[str | None] = mapped_column(String(255))
    findings: Mapped[str | None] = mapped_column(Text)
    confidentiality_status: Mapped[str] = mapped_column(String(50), default="confidential")


class AnnualCollectionReport(Base):
    __tablename__ = "annual_collection_report"

    report_id: Mapped[str] = pk()
    provincial_office_id: Mapped[str] = fk("provincial_office.provincial_office_id")
    fiscal_year: Mapped[int] = mapped_column(Integer, index=True)
    total_collections: Mapped[float | None] = mapped_column(Money)
    submission_date: Mapped[dt.date | None] = mapped_column(Date)
    posting_date: Mapped[dt.date | None] = mapped_column(Date)
