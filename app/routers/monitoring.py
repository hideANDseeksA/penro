"""Monitoring, examination of books and annual reporting (Sec. 10-12)."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.crud import build_crud_router
from app.core.permission import ENFORCEMENT, MONITORING, TREASURY
from app.models.monitoring import (
    AnnualCollectionReport,
    BooksExaminationRecord,
    ProvincialMonitoringRecord,
)

router = APIRouter()

router.include_router(
    build_crud_router(ProvincialMonitoringRecord, prefix="/monitoring-records",
                      tag="monitoring", write_roles=MONITORING)
)
# Sec. 11: examination findings are confidential and used solely for tax
# administration, so reads are narrower than the rest of the monitoring domain.
router.include_router(
    build_crud_router(BooksExaminationRecord, prefix="/books-examinations", tag="examinations",
                      write_roles=TREASURY, read_roles=ENFORCEMENT)
)
router.include_router(
    build_crud_router(AnnualCollectionReport, prefix="/annual-collection-reports",
                      tag="reporting", write_roles=TREASURY)
)
