"""Reference data: minerals, operation types, document types, offices, agencies."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.crud import build_crud_router
from app.core.permission import ADMIN, TREASURY
from app.models.mining import Mineral, MiningOperationType
from app.models.monitoring import NationalAgency, ProvincialOffice
from app.models.remedy import RemedyType
from app.models.shipment import DocumentType

router = APIRouter()

# MINERAL keeps mineral_category and ordinary_quarry_resource_excluded separate:
# ordinary quarry resources are exempt, but silica, clay and marble shipped out
# stay covered (Sec. 5a).
router.include_router(
    build_crud_router(Mineral, prefix="/minerals", tag="reference", write_roles=TREASURY)
)
router.include_router(
    build_crud_router(MiningOperationType, prefix="/mining-operation-types", tag="reference",
                      write_roles=(ADMIN,), allow_delete=True)
)
# DOCUMENT_TYPE is seeded from the Sec. 8(b)/8(c) matrix; edit with care.
router.include_router(
    build_crud_router(DocumentType, prefix="/document-types", tag="reference",
                      write_roles=(ADMIN,), allow_delete=True)
)
router.include_router(
    build_crud_router(RemedyType, prefix="/remedy-types", tag="reference",
                      write_roles=(ADMIN,), allow_delete=True)
)
router.include_router(
    build_crud_router(ProvincialOffice, prefix="/provincial-offices", tag="reference",
                      write_roles=(ADMIN,))
)
router.include_router(
    build_crud_router(NationalAgency, prefix="/national-agencies", tag="reference",
                      write_roles=(ADMIN,))
)
