"""End-to-end check of the ordinance flow: apply -> provisional -> issue ->
finalize -> penalties, plus auth, CSRF, API key, pagination and filtering."""
from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient

from app.main import app
from app.service import tax_computation as tax

API_KEY = {"X-API-Key": "dev-key-treasurer"}


def login(client: TestClient) -> dict:
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "ChangeMeNow!2026"},
                    headers=API_KEY)
    assert r.status_code == 200, r.text
    return {**API_KEY, "X-CSRF-Token": r.json()["csrf_token"]}


def test_full_lifecycle():
    client = TestClient(app)

    # --- API key is mandatory ---
    assert client.get("/api/v1/taxpayers").status_code == 401

    h = login(client)

    # --- CSRF required on writes ---
    no_csrf = client.post("/api/v1/minerals", json={"mineral_name": "X", "mineral_category": "other"},
                          headers=API_KEY)
    assert no_csrf.status_code == 403

    # --- pagination + server-side filtering ---
    r = client.get("/api/v1/document-types", params={"stage": "provisional", "mineral_scope": "iron_ore",
                                                     "size": 2, "page": 1}, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 4 and body["size"] == 2 and body["has_next"] is True
    assert len(body["items"]) == 2

    bad = client.get("/api/v1/document-types", params={"nope__eq": "x"}, headers=h)
    assert bad.status_code == 422

    ilike = client.get("/api/v1/document-types", params={"document_name__ilike": "bullion"}, headers=h)
    assert ilike.json()["total"] >= 1

    # --- fetch demo shipment ---
    shipment = client.get("/api/v1/shipments", params={"size": 1}, headers=h).json()["items"][0]
    sid = shipment["shipment_id"]

    # --- clearance blocked while Sec. 8(b) documents are missing ---
    apply_payload = {"shipment_id": sid, "estimated_gross_receipts": "10000000.00"}
    r = client.post("/api/v1/clearances/apply", json=apply_payload, headers=h)
    assert r.status_code == 422
    assert len(r.json()["detail"]["missing"]) == 4

    # --- attach the four provisional iron-ore documents ---
    doc_types = client.get("/api/v1/document-types",
                           params={"stage": "provisional", "mineral_scope": "iron_ore", "size": 10},
                           headers=h).json()["items"]
    for dtype in doc_types:
        r = client.post("/api/v1/shipment-documents", headers=h, json={
            "shipment_id": sid, "document_type_id": dtype["document_type_id"],
            "document_number": "DOC-1", "document_date": str(dt.date.today()),
            "document_status": "submitted",
        })
        assert r.status_code == 201, r.text

    # --- provisional assessment: 50% of 1% of 10,000,000 = 50,000 (Sec. 8b) ---
    r = client.post("/api/v1/clearances/apply", json=apply_payload, headers=h)
    assert r.status_code == 201, r.text
    result = r.json()
    assert result["provisional_tax_due"] == "50000.00"
    clearance_id, assessment_id = result["clearance_id"], result["assessment_id"]

    # --- clearance withheld until the provisional tax is paid ---
    assert client.post(f"/api/v1/clearances/{clearance_id}/issue", headers=h).status_code == 409
    r = client.post(f"/api/v1/assessments/{assessment_id}/payments", headers=h,
                    json={"amount_paid": "50000.00", "payment_type": "provisional"})
    assert r.status_code == 201 and r.json()["balance"] == "0.00"
    r = client.post(f"/api/v1/clearances/{clearance_id}/issue", headers=h)
    assert r.status_code == 200 and r.json()["within_3_working_days"] is True

    # --- finalize: actual gross receipts 12,000,000 -> tax 120,000, balance 70,000 (Sec. 8c) ---
    final_types = client.get("/api/v1/document-types",
                             params={"stage": "final", "mineral_scope": "iron_ore", "size": 10},
                             headers=h).json()["items"]
    for dtype in final_types:
        client.post("/api/v1/shipment-documents", headers=h, json={
            "shipment_id": sid, "document_type_id": dtype["document_type_id"],
            "document_number": "FIN-1", "document_status": "submitted",
        })
    r = client.post(f"/api/v1/shipments/{sid}/finalize", headers=h,
                    json={"gross_receipts": "12000000.00", "final_volume": "51000.000"})
    assert r.status_code == 200, r.text
    fin = r.json()
    assert fin["total_tax_at_1_percent"] == "120000.00"
    assert fin["balance_due"] == "70000.00"
    final_assessment = fin["assessment_id"]

    # --- Sec. 14 penalties: 25% surcharge + 2%/month, capped at 36 months ---
    due = dt.date.today() - dt.timedelta(days=95)
    r = client.post(f"/api/v1/assessments/{final_assessment}/recompute-penalties",
                    params={"due_date": due.isoformat()}, headers=h)
    pen = r.json()
    assert pen["surcharge"] == "17500.00"          # 25% of 70,000
    assert pen["interest_months_applied"] in (3, 4)
    assert pen["interest_capped_at_36_months"] is False

    # --- summary ties out ---
    summary = client.get(f"/api/v1/shipments/{sid}/tax-summary", headers=h).json()
    assert summary["gross_receipts"] == "12000000.00"
    assert len(summary["assessments"]) == 2

    # --- audit trail was written ---
    logs = client.get("/api/v1/audit-logs", params={"action": "clearance_issue"}, headers=h).json()
    assert logs["total"] >= 1


def test_tax_math_units():
    assert tax.full_tax("12000000") == tax.money("120000")
    assert tax.provisional_tax("10000000") == tax.money("50000")
    capped = tax.surcharge_and_interest("100000", dt.date(2020, 1, 1), dt.date(2026, 1, 1))
    assert capped["months"] == 36 and capped["capped"] is True
    # 100,000 + 25,000 surcharge; interest = 125,000 * 2% * 36 = 90,000
    assert capped["interest"] == tax.money("90000")
    assert tax.return_due_date("2026Q1") == dt.date(2026, 4, 20)
