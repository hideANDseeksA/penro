"""Date helpers for the ordinance's statutory clocks.

Kept out of the tax service so the deadline arithmetic can be unit-tested and
adjusted (e.g. a provincial holiday calendar) without touching tax math.
"""
from __future__ import annotations

import datetime as dt


def add_working_days(start: dt.date, days: int) -> dt.date:
    """Weekends excluded. Provincial and national holidays are not yet modeled
    — that needs a holiday table the ERD does not currently carry."""
    current, added = start, 0
    while added < days:
        current += dt.timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def quarter_of(date: dt.date) -> str:
    return f"{date.year}Q{(date.month - 1) // 3 + 1}"


def quarter_end(period: str) -> dt.date:
    """'2026Q1' -> 2026-03-31."""
    year, quarter = int(period[:4]), int(period[-1])
    month = quarter * 3
    return dt.date(year, month, 31 if month in (3, 12) else 30)


def months_elapsed(due_date: dt.date, as_of: dt.date) -> int:
    """Whole-and-started months, floored at 0. A started month counts in full,
    the usual LGC practice for Sec. 168 interest; the IRR should confirm."""
    if as_of <= due_date:
        return 0
    months = (as_of.year - due_date.year) * 12 + (as_of.month - due_date.month)
    if as_of.day > due_date.day:
        months += 1
    return max(months, 1)
