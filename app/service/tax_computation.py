"""Tax math and statutory clocks, straight from the ordinance.

Every constant here traces to a section; do not tune them without a
corresponding amendment to the ordinance text.
"""
from __future__ import annotations

import datetime as dt
from decimal import ROUND_HALF_UP, Decimal

from app.utils.date_utils import add_working_days, months_elapsed, quarter_end, quarter_of

__all__ = [
    "TAX_RATE", "PROVISIONAL_SHARE", "SURCHARGE_RATE", "INTEREST_RATE_PER_MONTH",
    "MAX_INTEREST_MONTHS", "FINE_MIN", "FINE_MAX", "money", "full_tax", "provisional_tax",
    "surcharge_and_interest", "return_due_date", "add_working_days", "quarter_of", "quarter_end",
    "months_elapsed",
]

# Sec. 7 - flat 1% of Gross Receipts.
TAX_RATE = Decimal("0.01")
# Sec. 8(b) - provisional payment is 50% of the 1% tax on ESTIMATED gross receipts.
PROVISIONAL_SHARE = Decimal("0.50")
# Sec. 14 - 25% surcharge, 2%/month interest, interest capped at 36 months.
SURCHARGE_RATE = Decimal("0.25")
INTEREST_RATE_PER_MONTH = Decimal("0.02")
MAX_INTEREST_MONTHS = 36
# Sec. 15(a) - fine range per violation.
FINE_MIN = Decimal("1000.00")
FINE_MAX = Decimal("5000.00")

# Deadlines (days unless noted)
FINAL_DOCUMENTS_DAYS = 15        # Sec. 8(c) - from issuance of final documents
BALANCE_PAYMENT_DAYS = 30        # Sec. 8(c) - from provisional payment or reassessment
QUARTERLY_RETURN_DAYS = 20       # Sec. 8(d) - after each calendar quarter
CLEARANCE_ISSUANCE_WORKING_DAYS = 3   # Sec. 9
PROTEST_FILING_DAYS = 60         # Sec. 13
PROTEST_DECISION_DAYS = 60       # Sec. 13
APPEAL_DAYS = 30                 # Sec. 13
REFUND_CLAIM_YEARS = 2           # Sec. 13 / Sec. 196 LGC

CENTS = Decimal("0.01")


def money(value: Decimal | float | int | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(CENTS, rounding=ROUND_HALF_UP)


def full_tax(gross_receipts: Decimal | float) -> Decimal:
    """Sec. 7: 1% of Gross Receipts. Gross Receipts is the contract value with
    no deduction for extraction, processing, transport or marketing (Sec. 6b)."""
    return money(Decimal(str(gross_receipts)) * TAX_RATE)


def provisional_tax(estimated_gross_receipts: Decimal | float) -> Decimal:
    """Sec. 8(b): 50% of the 1% tax on estimated gross receipts."""
    return money(Decimal(str(estimated_gross_receipts)) * TAX_RATE * PROVISIONAL_SHARE)


def surcharge_and_interest(
    unpaid_tax: Decimal | float, due_date: dt.date, as_of: dt.date | None = None
) -> dict:
    """Sec. 14: 25% surcharge, then 2%/month on tax + surcharge, max 36 months."""
    as_of = as_of or dt.date.today()
    tax = money(unpaid_tax)
    if tax <= 0:
        return {"surcharge": money(0), "interest": money(0), "months": 0, "total_due": money(0)}
    surcharge = money(tax * SURCHARGE_RATE)
    months = min(months_elapsed(due_date, as_of), MAX_INTEREST_MONTHS)
    interest = money((tax + surcharge) * INTEREST_RATE_PER_MONTH * months)
    return {
        "surcharge": surcharge,
        "interest": interest,
        "months": months,
        "capped": months_elapsed(due_date, as_of) > MAX_INTEREST_MONTHS,
        "total_due": money(tax + surcharge + interest),
    }


def return_due_date(period: str) -> dt.date:
    """Sec. 8(d): within 20 days after the close of each calendar quarter."""
    return quarter_end(period) + dt.timedelta(days=QUARTERLY_RETURN_DAYS)
