"""Payments, final reconciliation and Sec. 14 penalties."""
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
from app.models.assessment import TaxAssessment, TaxPayment
from app.models.clearance import ProvincialSoilDepletionTaxClearance
from app.models.shipment import Shipment
from app.service.assessment_service import balance_of, first_payment_date, total_paid
from app.service.document_requirements import missing_documents
from app.utils.security import assert_owns
from app.core.crud import build_crud_router

router = APIRouter(tags=["assessments"])


# Final reconciliation - Sec. 8(c)
class PaymentIn(BaseModel):
    amount_paid: Decimal = Field(gt=0)
    payment_date: dt.date | None = None
    payment_type: str = Field("provisional", pattern="^(provisional|final|penalty)$")


@router.post("/assessments/{assessment_id}/payments", status_code=201)
def record_payment(
    assessment_id: str,
    payload: PaymentIn,
    request: Request,
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(require_roles(*TREASURY)),
):
    """Record a TAX_PAYMENT against an assessment."""
    assessment = db.get(TaxAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "assessment not found")
    clearance = db.scalar(
        select(ProvincialSoilDepletionTaxClearance).where(
            ProvincialSoilDepletionTaxClearance.shipment_id == assessment.shipment_id
        )
    )
    payment = TaxPayment(
        taxpayer_id=assessment.taxpayer_id,
        assessment_id=assessment.assessment_id,
        clearance_id=clearance.clearance_id if clearance else None,
        payment_date=payload.payment_date or dt.date.today(),
        amount_paid=payload.amount_paid,
        payment_type=payload.payment_type,
    )
    db.add(payment)
    db.flush()
    record_audit(db, request=request, user_id=user.user_id, action="payment",
                 entity_name="tax_payment", entity_id=payment.payment_id,
                 details={"amount_paid": str(payload.amount_paid)})
    return {"payment_id": str(payment.payment_id), "balance": str(balance_of(db, assessment))}


class FinalizeIn(BaseModel):
    gross_receipts: Decimal = Field(gt=0, description="Actual contract value, no cost deductions (Sec. 6b)")
    final_volume: Decimal | None = None
    final_documents_issued_on: dt.date | None = None
    exported: bool = True


@router.post("/shipments/{shipment_id}/finalize")
def finalize_shipment(
    shipment_id: str,
    payload: FinalizeIn,
    request: Request,
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(require_roles(*TREASURY)),
):
    """Reconcile provisional to final tax (Sec. 8c).

    Final documents are due within 15 days of their issuance and the balance
    within 30 days of the provisional payment or reassessment, whichever comes
    first. Overpayment becomes a Refund/Credit remedy (Sec. 13).
    """
    shipment = db.get(Shipment, shipment_id)
    if shipment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "shipment not found")

    missing = missing_documents(db, shipment, "final", exported=payload.exported)
    if missing:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"detail": "Incomplete final documents (Sec. 8c)", "missing": missing},
        )

    provisional = db.scalar(
        select(TaxAssessment).where(
            TaxAssessment.shipment_id == shipment_id, TaxAssessment.assessment_stage == "provisional"
        )
    )
    provisional_paid = total_paid(db, provisional.assessment_id) if provisional else Decimal("0")

    shipment.gross_receipts = payload.gross_receipts
    if payload.final_volume is not None:
        shipment.final_volume = payload.final_volume
    shipment.shipment_status = "finalized"

    total_tax = tax.full_tax(payload.gross_receipts)
    final = TaxAssessment(
        taxpayer_id=shipment.taxpayer_id,
        shipment_id=shipment.shipment_id,
        estimated_gross_receipts=provisional.estimated_gross_receipts if provisional else None,
        gross_receipts=payload.gross_receipts,
        tax_rate=tax.TAX_RATE,
        tax_due=tax.money(total_tax - provisional_paid),
        surcharge=Decimal("0"),
        interest=Decimal("0"),
        assessment_stage="final",
        assessment_date=dt.date.today(),
    )
    db.add(final)
    db.flush()

    provisional_payment_date = first_payment_date(db, provisional.assessment_id) if provisional else None
    balance_due_date = (provisional_payment_date or dt.date.today()) + dt.timedelta(
        days=tax.BALANCE_PAYMENT_DAYS
    )
    overpaid = final.tax_due < 0

    record_audit(db, request=request, user_id=user.user_id, action="finalize",
                 entity_name="tax_assessment", entity_id=final.assessment_id,
                 details={"gross_receipts": str(payload.gross_receipts)})

    return {
        "assessment_id": str(final.assessment_id),
        "gross_receipts": str(tax.money(payload.gross_receipts)),
        "total_tax_at_1_percent": str(total_tax),
        "provisional_paid": str(provisional_paid),
        "balance_due": str(final.tax_due if not overpaid else Decimal("0")),
        "excess_payment": str(abs(final.tax_due) if overpaid else Decimal("0")),
        "balance_due_date": balance_due_date,
        "final_documents_deadline": (
            payload.final_documents_issued_on + dt.timedelta(days=tax.FINAL_DOCUMENTS_DAYS)
            if payload.final_documents_issued_on else None
        ),
        "note": ("Excess is creditable against succeeding liabilities or refundable "
                 "under Sec. 196 LGC — file a Refund/Credit remedy (Sec. 13).")
        if overpaid else "Balance payable within 30 days (Sec. 8c).",
    }


@router.post("/assessments/{assessment_id}/recompute-penalties")
def recompute_penalties(
    assessment_id: str,
    request: Request,
    due_date: dt.date = Query(..., description="Date the tax became due"),
    as_of: dt.date | None = Query(None),
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(require_roles(*TREASURY)),
):
    """Apply Sec. 14: 25% surcharge and 2%/month interest on the unpaid tax
    (interest computed on tax + surcharge), capped at 36 months."""
    assessment = db.get(TaxAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "assessment not found")

    unpaid = balance_of(db, assessment)
    result = tax.surcharge_and_interest(unpaid, due_date, as_of)
    assessment.surcharge = result["surcharge"]
    assessment.interest = result["interest"]
    db.flush()
    record_audit(db, request=request, user_id=user.user_id, action="recompute_penalties",
                 entity_name="tax_assessment", entity_id=assessment_id, details=result)
    return {
        "assessment_id": assessment_id,
        "unpaid_tax": str(unpaid),
        "surcharge": str(result["surcharge"]),
        "interest": str(result["interest"]),
        "interest_months_applied": result["months"],
        "interest_capped_at_36_months": result.get("capped", False),
        "total_due": str(result["total_due"]),
    }


@router.get("/shipments/{shipment_id}/tax-summary")
def tax_summary(
    shipment_id: str,
    db: Session = Depends(db_session),
    user: CurrentUser = Depends(get_current_user),
):
    """Assessed vs paid across every assessment on a shipment."""
    shipment = db.get(Shipment, shipment_id)
    if shipment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "shipment not found")
    assert_owns(user, shipment.taxpayer_id, "Not your shipment")

    rows = []
    assessed_sum = paid_sum = Decimal("0")
    for a in db.scalars(select(TaxAssessment).where(TaxAssessment.shipment_id == shipment_id)):
        paid = total_paid(db, a.assessment_id)
        assessed = tax.money(a.tax_due) + tax.money(a.surcharge) + tax.money(a.interest)
        assessed_sum += assessed
        paid_sum += paid
        rows.append({
            "assessment_id": str(a.assessment_id),
            "stage": a.assessment_stage,
            "tax_due": str(tax.money(a.tax_due)),
            "surcharge": str(tax.money(a.surcharge)),
            "interest": str(tax.money(a.interest)),
            "paid": str(paid),
            "balance": str(tax.money(assessed - paid)),
        })
    return {
        "shipment_id": shipment_id,
        "gross_receipts": str(tax.money(shipment.gross_receipts)),
        "assessments": rows,
        "total_assessed": str(tax.money(assessed_sum)),
        "total_paid": str(tax.money(paid_sum)),
        "total_balance": str(tax.money(assessed_sum - paid_sum)),
    }


router.include_router(
    build_crud_router(TaxAssessment, prefix="/assessments", tag="assessments",
                      write_roles=TREASURY, taxpayer_scoped=True)
)
router.include_router(
    build_crud_router(TaxPayment, prefix="/payments", tag="assessments",
                      write_roles=TREASURY, taxpayer_scoped=True)
)
