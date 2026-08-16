"""Mining operations, permits, sites and extraction records (Sec. 4-5, Sec. 10)."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.crud import build_crud_router
from app.core.permission import MONITORING, TREASURY
from app.models.mining import (
    ExtractionRecord,
    ExtractionSite,
    MiningOperation,
    PermitAuthority,
)

router = APIRouter()

router.include_router(
    build_crud_router(MiningOperation, prefix="/mining-operations", tag="mining",
                      write_roles=TREASURY, taxpayer_scoped=True)
)
# PERMIT_AUTHORITY records the MPSA/FTAA/SSMC/OTP authority a national or PMRB
# body issued — the Province records it, it does not grant it (Sec. 3e).
router.include_router(
    build_crud_router(PermitAuthority, prefix="/permit-authorities", tag="mining",
                      write_roles=MONITORING)
)
router.include_router(
    build_crud_router(ExtractionSite, prefix="/extraction-sites", tag="mining",
                      write_roles=MONITORING)
)
# EXTRACTION_RECORD covers all extraction, shipped or not — PENRO's Sec. 10 duty.
router.include_router(
    build_crud_router(ExtractionRecord, prefix="/extraction-records", tag="mining",
                      write_roles=MONITORING)
)
