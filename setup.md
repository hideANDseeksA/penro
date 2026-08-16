# Camarines Norte Soil Depletion Tax System — API

FastAPI + SQLAlchemy 2.0 + Alembic implementation of the schema and business
rules in `camarines_norte_soil_depletion_tax_erd_full.md` and the Camarines
Norte Soil Depletion Tax Ordinance of 2026.

Entity and field names match the ERD verbatim. Table names are the lower-cased
entity names (`TAXPAYER` → `taxpayer`, `PROVINCIAL_SOIL_DEPLETION_TAX_CLEARANCE`
→ `provincial_soil_depletion_tax_clearance`).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set DATABASE_URL and SECRET_KEY

alembic upgrade head
python -m app.seed              # SEED_DEMO=1 to also add a demo taxpayer/shipment
uvicorn app.main:app --reload   # docs at http://127.0.0.1:8000/docs
pytest -q
```

Or with Docker:

```bash
docker build -t soil-depletion-tax-api .
docker run --env-file .env -p 8000:8000 soil-depletion-tax-api
# run migrations as a separate step so a rolling deploy never races replicas:
docker run --env-file .env soil-depletion-tax-api alembic upgrade head
```

## Layout

```
.github/
  issues/user_stories.md      stories mapped to ordinance sections
  workflows/ci.yml            tests + migrations on PostgreSQL and MySQL + docker build
alembic/
  env.py                      reads DATABASE_URL from settings, renders GUID() portably
  versions/0001_initial_schema.py   all 30 tables
app/
  main.py                     app assembly, middleware, /health
  seed.py                     offices, roles, remedy types, Sec. 8 document matrix
  auth/
    models.py                 ROLE, SYSTEM_USER, AUDIT_LOG
    schemas.py                login and user-management schemas
  core/
    api_key.py                X-API-Key parsing and enforcement
    bucket.py                 token-bucket store
    columns.py                pk()/fk() column helpers
    config.py                 settings (.env)
    crud.py                   generic CRUD router factory
    crypto.py                 password hashing, session signing
    database.py               engine, session, Base
    permission.py             role constants and require_roles()
    security.py               session cookie, CSRF, current user
    types.py                  GUID, Money/Volume/Rate decimals
  models/                     one module per ERD domain
    taxpayer.py mining.py shipment.py clearance.py assessment.py
    tax_return.py remedy.py enforcement.py monitoring.py
  routers/
    auth.py admin.py audit.py taxpayer.py mining.py shipment.py
    clearance.py assessment.py tax_return.py remedy.py enforcement.py
    monitoring.py reference.py
  schemas/
    pagination.py             Page envelope and PageParams
    factory.py                pydantic schemas generated from the models
  service/
    tax_computation.py        Sec. 6-8, 13, 14, 15 constants and math
    document_requirements.py  Sec. 8(b)/8(c) matrix by mineral type
    assessment_service.py     paid/balance arithmetic
    audit_service.py          AUDIT_LOG writer
  utils/
    rate_limiter.py           middleware + login limiter
    query_filters.py          filter/sort/paginate engine
    date_utils.py             working days, quarters, month counting
    cache.py                  TTL cache for reference data
    security.py               ownership assertions, client IP
tests/
  conftest.py                 throwaway SQLite database per run
  test_flow.py                end-to-end lifecycle test
ui/read.md                    front-end integration notes
Dockerfile
```

## Security model

Three layers, all required together on `/api/v1/*`:

1. **`X-API-Key`** — enforced on the whole `/api/v1` tree including login.
   Keys come from the `API_KEYS` setting as `key:label:requests_per_minute`,
   so the treasurer portal and a PENRO client can carry different budgets.
2. **Session cookie** — `POST /api/v1/auth/login` sets `sdt_session`, an
   HttpOnly signed JWT, plus `sdt_csrf`, a readable CSRF token.
3. **CSRF double-submit** — every POST/PATCH/DELETE must echo the CSRF cookie
   in the `X-CSRF-Token` header, or it is rejected with 403.

Authorization is by `ROLE.role_name` (`Admin`, `Treasurer Staff`, `PENRO Staff`,
`PMRB Staff`, `Legal Office`, `Taxpayer`). Portal users with role `Taxpayer`
are scoped to rows carrying their own `taxpayer_id`. `SYSTEM_USER`, `ROLE` and
`AUDIT_LOG` are implementation infrastructure, not ordinance requirements.

Set `COOKIE_SECURE=true` and a real `SECRET_KEY` before any deployment. CORS is
configured with `allow_credentials=True` and an explicit origin list, which the
cookie flow requires.

## Rate limiting

Token bucket in `utils/rate_limiter.py`, keyed by API key when present and by
client IP otherwise. Responses carry `X-RateLimit-Limit` and
`X-RateLimit-Remaining`; a 429 carries `Retry-After`. Login has a tighter
per-IP limit (`RATE_LIMIT_LOGIN_PER_MINUTE`, default 5).

State is in-process. With more than one uvicorn worker, replace
`MemoryBucketStore` in `core/bucket.py` with a Redis-backed store — `hit(key,
rate, burst)` is the only method a replacement has to implement.

## Pagination and server-side filtering

Every list endpoint accepts the same query grammar and returns
`{items, page, size, total, pages, has_next, has_prev}`:

```
GET /api/v1/shipments
  ?page=2&size=50
  &sort=-shipment_date,buyer
  &shipment_status=cleared
  &shipment_date__gte=2026-01-01&shipment_date__lte=2026-03-31
  &gross_receipts__gt=1000000
  &buyer__ilike=steel
  &shipment_status__in=declared,cleared
  &final_volume__isnull=true
  &q=larap
```

Operators: `eq` (default), `ne`, `gt`, `gte`, `lt`, `lte`, `like`, `ilike`,
`in`, `isnull`. Filtering, sorting, and the count all run in SQL. Unknown
fields or operators return 422 rather than silently returning the unfiltered
table. `ilike` is implemented with `lower()` so MySQL and PostgreSQL behave
identically.

## MySQL / PostgreSQL portability

- UUID primary keys use `app.core.types.GUID`: native `uuid` on PostgreSQL,
  `CHAR(36)` on MySQL, `CHAR(36)` on SQLite for tests.
- Every `String` column has an explicit length (MySQL rejects unbounded
  `VARCHAR` in indexes).
- Money is `DECIMAL(18,2)`, volume `DECIMAL(18,3)`, tax rate `DECIMAL(9,6)` —
  never float, so 1% of a contract value reconciles to the centavo.
- `alembic/env.py` reads `DATABASE_URL` from settings (the `sqlalchemy.url` in
  `alembic.ini` is deliberately blank) and renders `GUID()` in generated
  migrations rather than the dialect type it resolved to.
- On MySQL, create the database as InnoDB/utf8mb4:
  `CREATE DATABASE soiltax CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
- Same migration, either engine: point `DATABASE_URL` at the target and run
  `alembic upgrade head`.

## Business endpoints and the rules they enforce

| Endpoint | Rule |
|---|---|
| `POST /clearances/apply` | Checks the provisional document list for the shipment's mineral type, then creates the provisional `TAX_ASSESSMENT` at 50% of the 1% tax on **estimated** gross receipts (Sec. 8b). Tax accrues at shipment and is collected on application (Sec. 8a). |
| `POST /assessments/{id}/payments` | Records `TAX_PAYMENT` and returns the running balance. |
| `POST /clearances/{id}/issue` | Refuses while the provisional tax is unpaid, and while any fine or sanction is unsettled (Sec. 15b). Reports whether issuance met the 3-working-day target (Sec. 9). |
| `POST /shipments/{id}/finalize` | Checks the final document list, computes 1% of actual gross receipts (Sec. 7), nets off the provisional payment, and returns the balance with its 30-day due date (Sec. 8c). Overpayment is routed to a Refund/Credit remedy. |
| `POST /assessments/{id}/recompute-penalties` | 25% surcharge, then 2%/month on tax + surcharge, interest capped at 36 months (Sec. 14). |
| `POST /returns` | Files the quarterly return, due 20 days after quarter close (Sec. 8d); flags late filing as a separate offense (Sec. 15a). |
| `POST /remedies` | Rejects a Protest filed past 60 days from assessment receipt, or a Refund/Credit past 2 years from payment (Sec. 13). |
| `POST /violations/{id}/sanctions` | Fines constrained to ₱1,000–₱5,000 per violation (Sec. 15a); the response repeats that paying a fine never excuses the underlying tax (Sec. 15e). |

Gross Receipts is always the actual contract value with no deduction for
extraction, processing, transport or marketing (Sec. 6b) — the API never
derives it from tonnage × a published price. The three mineral document lists
(iron ore / gold / other) are kept distinct at both the provisional and final
stage in `services/documents.py`.

## Deliberately not modeled

- Sec. 16 IRR issuance, Sec. 17 furnishing of copies, and Sec. 18 publication
  are one-time administrative acts, not transactional data.
- The clearance is a provincial revenue compliance document only. Nothing here
  grants the Province mining-regulatory power or authority over national
  permits (Sec. 3e, Sec. 9c).

## Notes and gaps worth flagging

- The ordinance does not fix the month-counting convention for Sec. 14
  interest. `tax.months_elapsed` counts a started month in full; the IRR
  (Sec. 16) should confirm it before go-live.
- `add_working_days` (Sec. 9) excludes weekends only. Provincial and national
  holidays need a holiday calendar, which the ERD does not currently carry — a
  small lookup table would be a reasonable proposed addition.
- The ERD's M:M lines between `MINING_OPERATION` and `EXTRACTION_SITE` /
  `MINERAL` are implemented as the association tables
  `mining_operation_extraction_site` and `mining_operation_mineral`. These are
  the only structures not literally named in the ERD.
- CI runs the migrations against both PostgreSQL and MySQL and fails if
  `alembic revision --autogenerate` still finds changes, which catches models
  drifting away from the migration history.
- `PENALTY_OR_ADMINISTRATIVE_SANCTION` carries an added `settled` boolean so
  Sec. 15(b) withholding of new clearances can be enforced. That is a proposed
  change to the ERD, not something in it today.
- This is not legal advice. Anything touching enforceability,
  constitutionality, or actual case handling should be reviewed by a licensed
  Philippine lawyer.
