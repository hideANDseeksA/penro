"""Seed reference data.

Run after `alembic upgrade head`:  python -m app.seed
Loads only what the ordinance itself fixes (offices, remedy types, document
types from the Sec. 8 matrix, national agencies) plus one demo taxpayer and
shipment when SEED_DEMO=1.
"""
from __future__ import annotations

import datetime as dt
import os
from decimal import Decimal

from sqlalchemy import select

from app.auth.models import Role, SystemUser
from app.core.crypto import hash_password
from app.core.database import SessionLocal
from app.models.mining import ExtractionSite, Mineral, MiningOperation, MiningOperationType
from app.models.monitoring import NationalAgency, ProvincialOffice
from app.models.remedy import RemedyType
from app.models.shipment import Shipment
from app.models.taxpayer import Taxpayer
from app.service.document_requirements import seed_document_types

ROLES = [
    ("Admin", "Full administrative access"),
    ("Treasurer Staff", "Provincial Treasurer's Office — assessment, collection, clearances"),
    ("PENRO Staff", "PENRO — extraction and shipment monitoring (Sec. 10)"),
    ("PMRB Staff", "PMRB — small-scale mining coordination"),
    ("Legal Office", "Provincial Legal Office — remedies and enforcement"),
    ("Taxpayer", "Taxpayer portal account"),
]

OFFICES = [
    ("Office of the Provincial Treasurer", "Assessment, collection, clearance issuance (Sec. 8-9, 11)"),
    ("PENRO", "Monitoring of extraction and shipment; Draft Survey Reports (Sec. 10)"),
    ("PMRB", "Small-scale mining board; OTP coordination (Sec. 7c)"),
    ("Provincial Legal Office", "IRR drafting input and enforcement (Sec. 16)"),
    ("Office of the Governor", "Clearance authority and sanctions (Sec. 9, 15b)"),
]

REMEDY_TYPES = [
    ("Protest", "60 days from receipt of assessment; Treasurer decides in 60 days; appeal in 30 (Sec. 13)"),
    ("Refund", "2 years from payment or entitlement (Sec. 13, Sec. 196 LGC)"),
    ("Credit", "2 years from payment or entitlement (Sec. 13, Sec. 196 LGC)"),
]

AGENCIES = ["DENR-MGB", "BSP", "Bureau of Customs", "Bureau of Local Government Finance"]

OPERATION_TYPES = [
    ("large-scale", "MPSA, FTAA, Exploration Permit with test-shipment authority, MPP (RA 7942)"),
    ("small-scale", "SSMC, Small-Scale Processing License (RA 7076 / PD 1899 / PMRB)"),
]

MINERALS = [
    ("Iron ore", "iron ore / bulk metallic", False),
    ("Gold doré", "gold bullion / doré / ore-concentrate", False),
    ("Silica", "non-metallic (shipped out — covered, Sec. 5a)", False),
    ("Sand and gravel", "ordinary quarry resource", True),
]


def main() -> None:
    db = SessionLocal()
    try:
        for name, description in ROLES:
            if not db.scalar(select(Role).where(Role.role_name == name)):
                db.add(Role(role_name=name, description=description))
        for name, role in OFFICES:
            if not db.scalar(select(ProvincialOffice).where(ProvincialOffice.office_name == name)):
                db.add(ProvincialOffice(office_name=name, office_role=role))
        for name, deadline in REMEDY_TYPES:
            if not db.scalar(select(RemedyType).where(RemedyType.remedy_name == name)):
                db.add(RemedyType(remedy_name=name, filing_deadline=deadline))
        for name in AGENCIES:
            if not db.scalar(select(NationalAgency).where(NationalAgency.agency_name == name)):
                db.add(NationalAgency(agency_name=name))
        for name, description in OPERATION_TYPES:
            if not db.scalar(select(MiningOperationType).where(MiningOperationType.name == name)):
                db.add(MiningOperationType(name=name, description=description))
        for name, category, quarry in MINERALS:
            if not db.scalar(select(Mineral).where(Mineral.mineral_name == name)):
                db.add(Mineral(mineral_name=name, mineral_category=category,
                               ordinary_quarry_resource_excluded=quarry))
        db.flush()
        seed_document_types(db)

        admin_role = db.scalar(select(Role).where(Role.role_name == "Admin"))
        treasury = db.scalar(select(ProvincialOffice).where(
            ProvincialOffice.office_name == "Office of the Provincial Treasurer"))
        if not db.scalar(select(SystemUser).where(SystemUser.username == "admin")):
            db.add(SystemUser(
                role_id=admin_role.role_id,
                provincial_office_id=treasury.provincial_office_id,
                username="admin",
                email="admin@camarinesnorte.gov.ph",
                password_hash=hash_password(os.getenv("SEED_ADMIN_PASSWORD", "ChangeMeNow!2026")),
            ))

        if os.getenv("SEED_DEMO") == "1":
            _seed_demo(db)

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


def _seed_demo(db) -> None:
    if db.scalar(select(Taxpayer).where(Taxpayer.taxpayer_name == "Demo Mining Corp.")):
        return
    taxpayer = Taxpayer(
        taxpayer_name="Demo Mining Corp.",
        taxpayer_type="Corporation",
        tax_identification_details="TIN 000-111-222-000",
        business_address="Jose Panganiban, Camarines Norte",
    )
    op_type = db.scalar(select(MiningOperationType).where(MiningOperationType.name == "large-scale"))
    site = ExtractionSite(site_name="Larap Pit 1", municipality="Jose Panganiban", barangay="Larap")
    mineral = db.scalar(select(Mineral).where(Mineral.mineral_name == "Iron ore"))
    db.add_all([taxpayer, site])
    db.flush()
    operation = MiningOperation(
        taxpayer_id=taxpayer.taxpayer_id,
        operation_type_id=op_type.operation_type_id,
        operation_name="Larap Iron Project",
        legal_basis="MPSA No. 000-00-V",
        status="active",
    )
    db.add(operation)
    db.flush()
    db.add(Shipment(
        taxpayer_id=taxpayer.taxpayer_id,
        mining_operation_id=operation.mining_operation_id,
        extraction_site_id=site.extraction_site_id,
        mineral_id=mineral.mineral_id,
        shipment_date=dt.date.today(),
        estimated_volume=Decimal("50000.000"),
        buyer="Overseas Steel Ltd.",
        destination="Port of Qingdao",
        shipment_status="declared",
    ))


if __name__ == "__main__":
    main()
