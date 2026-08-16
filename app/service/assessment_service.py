"""Assessment arithmetic shared by the clearance and assessment routers."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assessment import TaxAssessment, TaxPayment
from app.service import tax_computation as tax

# helpers
def total_paid(db: Session, assessment_id) -> Decimal:
    total = db.scalar(
        select(func.coalesce(func.sum(TaxPayment.amount_paid), 0)).where(
            TaxPayment.assessment_id == assessment_id
        )
    )
    return tax.money(total)


def balance_of(db: Session, assessment: TaxAssessment) -> Decimal:
    assessed = tax.money(assessment.tax_due) + tax.money(assessment.surcharge) + tax.money(assessment.interest)
    return tax.money(assessed - total_paid(db, assessment.assessment_id))


def first_payment_date(db: Session, assessment_id) -> dt.date | None:
    return db.scalar(
        select(func.min(TaxPayment.payment_date)).where(TaxPayment.assessment_id == assessment_id)
    )
