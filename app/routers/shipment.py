"""Shipments and their supporting documents (Sec. 6-8)."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.crud import build_crud_router
from app.core.permission import TAXPAYER, TREASURY
from app.models.monitoring import NationalAgencyDocument
from app.models.shipment import Shipment, ShipmentDocument

router = APIRouter()

router.include_router(
    build_crud_router(Shipment, prefix="/shipments", tag="shipments",
                      write_roles=(*TREASURY, TAXPAYER), taxpayer_scoped=True)
)
router.include_router(
    build_crud_router(ShipmentDocument, prefix="/shipment-documents", tag="shipments",
                      write_roles=(*TREASURY, TAXPAYER))
)
router.include_router(
    build_crud_router(NationalAgencyDocument, prefix="/national-agency-documents",
                      tag="shipments", write_roles=TREASURY)
)
