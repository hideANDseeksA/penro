"""Quarterly soil depletion tax return (Sec. 8d)."""
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
from app.models.tax_return import ReturnShipment, SoilDepletionTaxReturn
from app.utils.security import assert_owns
from app.core.crud import build_crud_router

router = APIRouter(tags=["returns"])


# Quarterly return - Sec. 8(d)
class ReturnShipmentIn(BaseModel):
    shipment_id: str
    reported_volume_shipped: Decimal | None = None
    otp_reference: str | None = None


class ReturnIn(BaseModel):
    taxpayer_id: str
    return_period: str = Field(pattern=r"^\d{4}Q[1-4]$", examples=["2026Q1"])
    reported_gross_receipts: Decimal | None = None
    filing_date: dt.date | None = None
    shipments: list[ReturnShipmentIn] = []


@router.post("/returns", status_code=201)
def file_return(
    payload: ReturnIn,
    request: Request,
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
):
    """File the quarterly SOIL_DEPLETION_TAX_RETURN — due within 20 days after
    the close of the quarter (Sec. 8d). Each shipment is itemized with its OTP
    reference. Late filing is flagged: each return filed in violation is a
    separate offense (Sec. 15a)."""
    assert_owns(user, payload.taxpayer_id, "Not your taxpayer record")

    filing_date = payload.filing_date or dt.date.today()
    due = tax.return_due_date(payload.return_period)
    late = filing_date > due

    tax_return = SoilDepletionTaxReturn(
        taxpayer_id=payload.taxpayer_id,
        return_period=payload.return_period,
        filing_date=filing_date,
        reported_gross_receipts=payload.reported_gross_receipts,
        return_status="filed_late" if late else "filed",
    )
    db.add(tax_return)
    db.flush()
    for line in payload.shipments:
        db.add(ReturnShipment(
            return_id=tax_return.return_id,
            shipment_id=line.shipment_id,
            reported_volume_shipped=line.reported_volume_shipped,
            otp_reference=line.otp_reference,
        ))
    db.flush()
    record_audit(db, request=request, user_id=user.user_id, action="file_return",
                 entity_name="soil_depletion_tax_return", entity_id=tax_return.return_id)
    return {
        "return_id": str(tax_return.return_id),
        "due_date": due,
        "filed_late": late,
        "note": ("Late filing is a separate offense per return (Sec. 15a); the fine is "
                 "₱1,000–₱5,000 and does not excuse the underlying tax.") if late else
                "Attach MGB Form 29-1 (gold) or 29-6 (iron) as required by Sec. 8(d).",
    }


router.include_router(
    build_crud_router(SoilDepletionTaxReturn, prefix="/returns", tag="returns",
                      write_roles=TREASURY, taxpayer_scoped=True)
)
router.include_router(
    build_crud_router(ReturnShipment, prefix="/return-shipments", tag="returns",
                      write_roles=(*TREASURY, "Taxpayer"))
)
