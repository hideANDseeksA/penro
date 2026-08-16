"""Taxpayer's remedies: protest, refund, credit (Sec. 13)."""
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
from app.models.remedy import RemedyType, TaxpayerRemedy
from app.utils.security import assert_owns
from app.core.crud import build_crud_router
from app.core.permission import ENFORCEMENT

router = APIRouter(tags=["remedies"])


# Remedies - Sec. 13
class RemedyIn(BaseModel):
    taxpayer_id: str
    remedy_type: str = Field(pattern="^(Protest|Refund|Credit)$")
    assessment_id: str | None = None
    filing_date: dt.date | None = None
    reference_date: dt.date | None = Field(
        None, description="Assessment receipt date for a Protest, or payment date for Refund/Credit"
    )


@router.post("/remedies", status_code=201)
def file_remedy(
    payload: RemedyIn,
    request: Request,
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
):
    """File a TAXPAYER_REMEDY. Protest: 60 days from receipt of the assessment,
    Treasurer decides within 60 days, appeal within 30 days of denial or lapse.
    Refund/credit: 2 years from payment (Sec. 13)."""
    assert_owns(user, payload.taxpayer_id, "Not your taxpayer record")

    remedy_type = db.scalar(select(RemedyType).where(RemedyType.remedy_name == payload.remedy_type))
    if remedy_type is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown remedy type {payload.remedy_type}")

    filing_date = payload.filing_date or dt.date.today()
    if payload.reference_date:
        if payload.remedy_type == "Protest":
            deadline = payload.reference_date + dt.timedelta(days=tax.PROTEST_FILING_DAYS)
            rule = "60 days from receipt of the assessment notice (Sec. 13)"
        else:
            deadline = payload.reference_date.replace(year=payload.reference_date.year + tax.REFUND_CLAIM_YEARS)
            rule = "2 years from payment or entitlement (Sec. 13, Sec. 196 LGC)"
        if filing_date > deadline:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Filed beyond the statutory period — {rule}. Deadline was {deadline.isoformat()}.",
            )
    else:
        deadline = None

    remedy = TaxpayerRemedy(
        taxpayer_id=payload.taxpayer_id,
        assessment_id=payload.assessment_id,
        remedy_type_id=remedy_type.remedy_type_id,
        filing_date=filing_date,
        status="filed",
    )
    db.add(remedy)
    db.flush()
    record_audit(db, request=request, user_id=user.user_id, action="file_remedy",
                 entity_name="taxpayer_remedy", entity_id=remedy.remedy_id)
    return {
        "remedy_id": str(remedy.remedy_id),
        "filing_deadline_checked_against": deadline,
        "treasurer_decision_due": filing_date + dt.timedelta(days=tax.PROTEST_DECISION_DAYS)
        if payload.remedy_type == "Protest" else None,
        "appeal_window_days": tax.APPEAL_DAYS if payload.remedy_type == "Protest" else None,
    }


router.include_router(
    build_crud_router(TaxpayerRemedy, prefix="/remedies", tag="remedies",
                      write_roles=ENFORCEMENT, taxpayer_scoped=True)
)
