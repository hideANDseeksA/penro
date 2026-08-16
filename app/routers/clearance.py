"""Clearance application and issuance (Sec. 8b, Sec. 9)."""
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
from app.models.assessment import TaxAssessment
from app.models.clearance import ProvincialSoilDepletionTaxClearance
from app.models.enforcement import PenaltyOrAdministrativeSanction, Violation
from app.models.shipment import Shipment
from app.service.assessment_service import balance_of
from app.service.document_requirements import missing_documents
from app.utils.date_utils import add_working_days
from app.utils.security import assert_owns
from app.core.crud import build_crud_router

router = APIRouter(tags=["clearances"])


# Clearance application - Sec. 8(b) + Sec. 9
class ClearanceApplication(BaseModel):
    shipment_id: str
    estimated_gross_receipts: Decimal = Field(gt=0, description="Estimated contract value (Sec. 6b)")
    application_date: dt.date | None = None
    exported: bool = True


class ClearanceApplicationResult(BaseModel):
    clearance_id: str
    assessment_id: str
    estimated_gross_receipts: Decimal
    provisional_tax_due: Decimal
    target_issuance_date: dt.date
    note: str


@router.post("/clearances/apply", response_model=ClearanceApplicationResult, status_code=201)
def apply_for_clearance(
    payload: ClearanceApplication,
    request: Request,
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
):
    """Apply for the PROVINCIAL_SOIL_DEPLETION_TAX_CLEARANCE.

    Creates the provisional TAX_ASSESSMENT at 50% of the 1% tax on estimated
    gross receipts (Sec. 8b) after checking the mineral-specific provisional
    document list. The tax accrues at the time of shipment and is collected on
    this application (Sec. 8a).
    """
    shipment = db.get(Shipment, payload.shipment_id)
    if shipment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "shipment not found")
    assert_owns(user, shipment.taxpayer_id, "Not your shipment")
    if shipment.clearance is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Shipment already has a clearance application")

    missing = missing_documents(db, shipment, "provisional", exported=payload.exported)
    if missing:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"detail": "Incomplete provisional documents (Sec. 8b)", "missing": missing},
        )

    application_date = payload.application_date or dt.date.today()
    assessment = TaxAssessment(
        taxpayer_id=shipment.taxpayer_id,
        shipment_id=shipment.shipment_id,
        estimated_gross_receipts=payload.estimated_gross_receipts,
        tax_rate=tax.TAX_RATE,
        tax_due=tax.provisional_tax(payload.estimated_gross_receipts),
        surcharge=Decimal("0"),
        interest=Decimal("0"),
        assessment_stage="provisional",
        assessment_date=application_date,
    )
    clearance = ProvincialSoilDepletionTaxClearance(
        taxpayer_id=shipment.taxpayer_id,
        shipment_id=shipment.shipment_id,
        application_date=application_date,
        clearance_status="applied",
    )
    db.add_all([assessment, clearance])
    db.flush()
    record_audit(db, request=request, user_id=user.user_id, action="clearance_apply",
                 entity_name="provincial_soil_depletion_tax_clearance", entity_id=clearance.clearance_id)

    return ClearanceApplicationResult(
        clearance_id=str(clearance.clearance_id),
        assessment_id=str(assessment.assessment_id),
        estimated_gross_receipts=tax.money(payload.estimated_gross_receipts),
        provisional_tax_due=assessment.tax_due,
        target_issuance_date=add_working_days(application_date, tax.CLEARANCE_ISSUANCE_WORKING_DAYS),
        note="Provisional payment is 50% of the 1% tax on estimated gross receipts (Sec. 8b).",
    )


@router.post("/clearances/{clearance_id}/issue")
def issue_clearance(
    clearance_id: str,
    request: Request,
    issuance_date: dt.date | None = None,
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(require_roles(*TREASURY)),
):
    """Issue the clearance (Sec. 9): only on complete submission and payment,
    and withheld while any fine, surcharge, interest or tax is unsettled
    (Sec. 15b). Target is 3 working days from complete application."""
    clearance = db.get(ProvincialSoilDepletionTaxClearance, clearance_id)
    if clearance is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "clearance not found")

    provisional = db.scalar(
        select(TaxAssessment).where(
            TaxAssessment.shipment_id == clearance.shipment_id,
            TaxAssessment.assessment_stage == "provisional",
        )
    )
    if provisional is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "No provisional assessment on this shipment")
    if balance_of(db, provisional) > 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "Provisional tax not fully paid (Sec. 8b)")

    unsettled = db.scalar(
        select(func.count())
        .select_from(PenaltyOrAdministrativeSanction)
        .join(Violation, Violation.violation_id == PenaltyOrAdministrativeSanction.violation_id)
        .where(
            Violation.taxpayer_id == clearance.taxpayer_id,
            PenaltyOrAdministrativeSanction.settled.is_(False),
        )
    )
    if unsettled:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "New clearances are withheld until tax, surcharge, interest and fines are settled (Sec. 15b)",
        )

    clearance.issuance_date = issuance_date or dt.date.today()
    clearance.clearance_status = "issued"
    db.flush()
    target = add_working_days(clearance.application_date, tax.CLEARANCE_ISSUANCE_WORKING_DAYS)
    record_audit(db, request=request, user_id=user.user_id, action="clearance_issue",
                 entity_name="provincial_soil_depletion_tax_clearance", entity_id=clearance.clearance_id)
    return {
        "clearance_id": str(clearance.clearance_id),
        "issuance_date": clearance.issuance_date,
        "within_3_working_days": clearance.issuance_date <= target,
        "note": "Provincial revenue compliance document only; it does not amend or "
                "supersede any national permit or transport authorization (Sec. 9c).",
    }


# Registry endpoints: paginated, filterable list/detail plus guarded writes.
router.include_router(
    build_crud_router(
        ProvincialSoilDepletionTaxClearance,
        prefix="/clearances",
        tag="clearances",
        write_roles=TREASURY,
        taxpayer_scoped=True,
    )
)
