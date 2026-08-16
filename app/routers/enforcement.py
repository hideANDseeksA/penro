"""Violations and sanctions (Sec. 15)."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.permission import TREASURY, require_roles
from app.core.security import CurrentUser, db_session, get_current_user
from app.service import tax_computation as tax
from app.service.audit_service import record_audit
from app.models.enforcement import PenaltyOrAdministrativeSanction, Violation
from app.core.crud import build_crud_router
from app.core.permission import ENFORCEMENT

router = APIRouter(tags=["enforcement"])


# Sanctions - Sec. 15
class SanctionIn(BaseModel):
    sanction_type: str = Field(pattern="^(fine|suspension|revocation|referral)$")
    fine_amount: Decimal | None = None
    sanction_date: dt.date | None = None


@router.post("/violations/{violation_id}/sanctions", status_code=201)
def impose_sanction(
    violation_id: str,
    payload: SanctionIn,
    request: Request,
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(require_roles(*TREASURY)),
):
    """Impose a PENALTY_OR_ADMINISTRATIVE_SANCTION. Fines run ₱1,000–₱5,000 per
    violation, and each shipment or return in violation is a separate offense
    (Sec. 15a). A single violation may carry a fine, a suspension and a referral
    at once."""
    violation = db.get(Violation, violation_id)
    if violation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "violation not found")

    if payload.sanction_type == "fine":
        if payload.fine_amount is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "fine_amount is required for a fine")
        if not (tax.FINE_MIN <= payload.fine_amount <= tax.FINE_MAX):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Fine must be between ₱{tax.FINE_MIN} and ₱{tax.FINE_MAX} per violation (Sec. 15a)",
            )

    sanction = PenaltyOrAdministrativeSanction(
        violation_id=violation_id,
        sanction_type=payload.sanction_type,
        fine_amount=payload.fine_amount,
        sanction_date=payload.sanction_date or dt.date.today(),
        settled=False,
    )
    db.add(sanction)
    db.flush()
    record_audit(db, request=request, user_id=user.user_id, action="impose_sanction",
                 entity_name="penalty_or_administrative_sanction", entity_id=sanction.sanction_id)
    return {
        "sanction_id": str(sanction.sanction_id),
        "note": "Payment of a fine or sanction does not relieve the offender of the "
                "underlying tax, surcharge and interest (Sec. 15e).",
    }


router.include_router(
    build_crud_router(Violation, prefix="/violations", tag="enforcement",
                      write_roles=ENFORCEMENT, taxpayer_scoped=True)
)
router.include_router(
    build_crud_router(PenaltyOrAdministrativeSanction, prefix="/sanctions", tag="enforcement",
                      write_roles=ENFORCEMENT)
)
