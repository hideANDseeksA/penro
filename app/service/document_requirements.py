"""Document requirements by mineral type and stage (Sec. 8b provisional,
Sec. 8c final). The three mineral scopes are kept distinct on purpose — the
ordinance lists different documents for iron ore, gold, and other minerals."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mining import Mineral
from app.models.shipment import DocumentType, Shipment, ShipmentDocument

IRON_ORE = "iron_ore"
GOLD = "gold"
OTHER = "other"

REQUIRED_DOCUMENTS: dict[tuple[str, str], list[str]] = {
    (IRON_ORE, "provisional"): [
        "OTP application/issuance (MGB Form 12-1)",
        "MGB Stockpile Validation or Field Verification Report",
        "Preliminary Draft Survey Report",
        "Sales/Marketing Contract or Pro-forma Invoice",
    ],
    (GOLD, "provisional"): [
        "OTP (MGB Form 12-1) explicitly covering gold",
        "MGB Bullion Shipment Inspection, Weighing & Sealing Report",
        "Preliminary Assay Report or buyer/refinery valuation",
    ],
    (OTHER, "provisional"): [
        "OTP",
        "Sales/Marketing Contract or Pro-forma Invoice",
        "Preliminary Assay Report or valuation",
    ],
    (IRON_ORE, "final"): [
        "Final Commercial Sales Invoice and Bill of Lading",
        "Final Draft Survey Report at port of discharge",
        "BOC Export Declaration and MGB MOEP (if exported)",
    ],
    (GOLD, "final"): [
        "BSP Gold Buying Station Delivery Receipt (or refinery receipt)",
        "BSP Final Assay Advice or certified refinery assay",
        "BSP Payment/Transaction Advice",
    ],
    (OTHER, "final"): [
        "OTP",
        "Sales Contract or Invoice",
        "Final Assay Report or valuation",
    ],
}

# Documents that are conditional rather than absolute (Sec. 8c iron ore).
OPTIONAL_IF_NOT_EXPORTED = {"BOC Export Declaration and MGB MOEP (if exported)"}


def mineral_scope(mineral: Mineral) -> str:
    """Map MINERAL.mineral_category onto the ordinance's three document lists."""
    category = (mineral.mineral_category or "").strip().lower()
    if "iron" in category or category in {"bulk metallic", "bulk_metallic"}:
        return IRON_ORE
    if "gold" in category or "bullion" in category or "dore" in category or "doré" in category:
        return GOLD
    return OTHER


def missing_documents(db: Session, shipment: Shipment, stage: str, *, exported: bool = True) -> list[str]:
    """Names of SHIPMENT_DOCUMENT rows still absent for this stage."""
    mineral = db.get(Mineral, shipment.mineral_id)
    scope = mineral_scope(mineral) if mineral else OTHER
    required = list(REQUIRED_DOCUMENTS[(scope, stage)])
    if not exported:
        required = [d for d in required if d not in OPTIONAL_IF_NOT_EXPORTED]

    submitted = set(
        db.scalars(
            select(DocumentType.document_name)
            .join(ShipmentDocument, ShipmentDocument.document_type_id == DocumentType.document_type_id)
            .where(
                ShipmentDocument.shipment_id == shipment.shipment_id,
                DocumentType.stage == stage,
                ShipmentDocument.document_status.in_(["submitted", "verified", "accepted"]),
            )
        )
    )
    return [name for name in required if name not in submitted]


def seed_document_types(db: Session) -> None:
    """Load DOCUMENT_TYPE from the Sec. 8 matrix (idempotent)."""
    existing = {
        (name, scope, stage)
        for name, scope, stage in db.execute(
            select(DocumentType.document_name, DocumentType.mineral_scope, DocumentType.stage)
        )
    }
    for (scope, stage), names in REQUIRED_DOCUMENTS.items():
        for name in names:
            if (name, scope, stage) not in existing:
                db.add(DocumentType(document_name=name, mineral_scope=scope, stage=stage))
    db.flush()
