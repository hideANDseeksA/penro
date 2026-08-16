# User stories — Soil Depletion Tax System

Each story cites the ordinance section it implements. Anything without a
section reference is implementation infrastructure and should be labelled
`infra`, not `ordinance`.

## Taxpayer registration and operations (Sec. 4–5)

- **As Treasurer staff**, I register a taxpayer with their type and tax
  identification details so shipments and assessments can be attributed.
  *Done when:* `TAXPAYER` created, appears in a filtered list, audit row written.
- **As Treasurer staff**, I record a mining operation with its type
  (large-scale under RA 7942, small-scale under RA 7076/PD 1899) and its
  `PERMIT_AUTHORITY` records, so coverage is documented.
  *Note:* the Province records the permit; it does not issue or validate it
  (Sec. 3e).
- **As Treasurer staff**, I mark a mineral as an ordinary quarry resource so it
  is excluded — while silica, clay and marble shipped out stay covered (Sec. 5a).

## Clearance and provisional payment (Sec. 8b, Sec. 9)

- **As a taxpayer**, I apply for a Provincial Soil Depletion Tax Clearance for a
  shipment and am told exactly which documents are still missing for my mineral
  type, so I am not rejected without a reason (Sec. 8b).
- **As a taxpayer**, I am assessed 50% of the 1% tax on my *estimated* gross
  receipts at application, not a tonnage-based figure (Sec. 6b, Sec. 7, Sec. 8b).
- **As Treasurer staff**, I cannot issue a clearance while the provisional tax
  is unpaid or any fine is unsettled (Sec. 8b, Sec. 15b).
- **As Treasurer staff**, I can see whether issuance met the 3-working-day
  target from complete application (Sec. 9).
- **As a taxpayer**, my clearance states plainly that it is a provincial revenue
  document and does not amend any national permit (Sec. 9c).

## Final reconciliation (Sec. 8c)

- **As Treasurer staff**, I finalise a shipment against the actual contract
  value, and the system nets the provisional payment off the 1% total and gives
  me the balance with its 30-day due date.
- **As a taxpayer**, when I overpaid, the system tells me the excess is
  creditable or refundable under Sec. 196 LGC rather than silently keeping it.
- **As Treasurer staff**, final documents are checked against the list for the
  mineral type — iron ore, gold, and other minerals differ.

## Quarterly returns (Sec. 8d)

- **As a taxpayer**, I file a quarterly return itemising each shipment with its
  OTP reference, and I am told the 20-day deadline and whether I met it.
- **As Treasurer staff**, a late return is flagged, because each return filed in
  violation is a separate offense (Sec. 15a).

## Remedies (Sec. 13)

- **As a taxpayer**, I file a protest within 60 days of receiving an assessment
  and the system refuses a late filing rather than accepting it into a dead end.
- **As a taxpayer**, I file a refund or credit claim within 2 years of payment.
- **As Legal Office staff**, I see when the Treasurer's 60-day decision period
  lapses and the 30-day appeal window that follows.

## Surcharges, interest, enforcement (Sec. 14–15)

- **As Treasurer staff**, unpaid tax draws a 25% surcharge and 2%/month interest
  on tax plus surcharge, and interest stops accruing at 36 months.
- **As Legal Office staff**, I record a violation against a shipment or a return
  and attach a fine, a suspension and a referral to the same violation.
- **As Legal Office staff**, a fine outside ₱1,000–₱5,000 per violation is
  rejected, and the response states that paying it does not excuse the tax.

## Monitoring and reporting (Sec. 10–12)

- **As PENRO staff**, I record extraction volumes for *all* extraction, whether
  or not it is ever shipped, and furnish Draft Survey Reports before shipment.
- **As Treasurer staff**, I record an examination of books with its
  confidentiality status (Sec. 11).
- **As Treasurer staff**, I render the annual collection report to the
  Sanggunian for posting under the full-disclosure policy (Sec. 12).

## Platform (infra — not ordinance requirements)

- **As any client**, I must present a valid `X-API-Key`, and my usage is limited
  per key with `X-RateLimit-*` headers and `Retry-After` on 429.
- **As a user**, I log in and receive an HttpOnly session cookie plus a CSRF
  token I echo on writes.
- **As Admin**, I read the audit log to answer "who issued this clearance" and
  "who approved this refund", and nobody can edit it through the API.
- **As any client**, every list endpoint is paginated and filterable server-side
  so I never pull a whole table to find one shipment.

## Open questions to resolve with the IRR (Sec. 16) or counsel

- Month-counting convention for Sec. 14 interest (a started month currently
  counts in full).
- Whether "working days" in Sec. 9 excludes provincial holidays; no holiday
  calendar exists in the ERD yet.
- Whether a partially settled fine should still block new clearances under
  Sec. 15b, or only an unsettled one.

Legal review by a licensed Philippine lawyer is required before any of these
behaviours are treated as authoritative.
