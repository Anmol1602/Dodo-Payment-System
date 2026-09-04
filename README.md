# Minimal Invoice & Payment Service

A production-grade, asynchronous backend microservice for invoicing, customer management, mock payment processing, and event-driven signed webhooks.

Built for the **Dodo Payments Backend Engineering** technical assessment.

---

## Language & Framework Justification

This service is implemented using **Python 3.10+ and FastAPI** with asynchronous PostgreSQL connectivity (`asyncpg` / `SQLAlchemy AsyncIO`).

### Why Python / FastAPI?
1. **Asynchronous Throughput:** Financial orchestration microservices are predominantly I/O-bound (database queries, network round-trips to PSPs, and webhook dispatches). FastAPI's non-blocking `asyncio` event loop handles high-concurrency requests with low memory footprints without thread starvation.
2. **Strict Typings & Pydantic v2:** Pydantic v2 core is compiled in Rust, providing ultra-fast serialization and rigorous validation of integer currency amounts, ensuring zero floating-point values enter the system.
3. **Ecosystem & Velocity:** Rich ecosystem for async database drivers, clean migration tooling (Alembic), and native OpenAPI 3.1 generation.

> **Note on Rust Preference:**  
> *While my current production experience is centered around high-performance Python/Go asynchronous systems, I have a strong interest in Rust's memory safety, type system, and zero-cost abstractions. I am very eager to learn Rust and transition high-throughput billing microservices to Axum or Actix.*

---

## Core Features

- **Multi-Tenant API Key Authentication:** Keys are prefixed (`dodo_live_...`), SHA-256 hashed at rest, scoped per business, and support instant revocation.
- **Customers & Invoices:** Create, retrieve, and filter customers and invoices. Invoices support line items (`quantity`, `unit_amount_cents`) with server-side total verification.
- **Strict Integer Minor Units (Cents):** No floats anywhere in the monetary path. All computations use standard 64-bit integers.
- **Rigorous State Machine:** Validates all state transitions (`draft` $\to$ `open` $\to$ `paid`, `void`, `uncollectible`). Rejects invalid transitions with clear structured errors. Terminal states (`paid`, `void`) are strictly immutable.
- **Mock Payment Processor (PSP):** Deterministic mock PSP supporting `tok_success`, `tok_insufficient_funds`, `tok_card_declined`, `tok_timeout` (30s delay handled cleanly by our 5s client timeout), and `tok_network_error`.
- **Idempotency Guarantees:** `Idempotency-Key` header with request fingerprinting and row-level database locking to prevent double charges.
- **Signed Asynchronous Webhooks:** Delivers `invoice.created`, `invoice.paid`, and `invoice.payment_failed` with HMAC-SHA256 signatures (`X-Dodo-Signature`) and automatic exponential backoff retries.

---

## Quickstart (`docker compose up`)

The entire stack (FastAPI Application, PostgreSQL 16 database, Alembic migrations, and Mock PSP) spins up with a single command with zero manual configuration.

```bash
# 1. Clone the repository
git clone <repo-url>
cd dodo-invoice-service

# 2. Start the service via Docker Compose
docker compose up --build
```

The service will:
1. Start PostgreSQL 16 on port `5432` and await health check readiness.
2. Run automated database migrations (`alembic upgrade head`).
3. Seed a default test business and API key for immediate testing.
4. Launch the FastAPI application and Mock PSP on `http://localhost:8000`.
5. Expose interactive Swagger documentation at `http://localhost:8000/docs`.

---

## Seeding & Test Credentials

On initialization, the database seeds the following test business and credentials:
* **Business Name:** Acme Cloud Inc.
* **Test API Key:** `dodo_live_testkey1234567890abcdef1234567890`

You can also create new businesses and generate new API keys via `POST /api/v1/auth/register`.

---

## Curl Walkthrough & Examples

### 1. Create a Customer

```bash
curl -s -X POST http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer dodo_live_testkey1234567890abcdef1234567890" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Connor",
    "email": "sarah@cyberdyne.com"
  }' | jq .
```

**Expected Response (HTTP 201 Created):**
```json
{
  "id": "c1f72810-7389-4a0b-932f-b42e718b5ef1",
  "business_id": "b0a11223-4455-6677-8899-aabbccddeeff",
  "name": "Sarah Connor",
  "email": "sarah@cyberdyne.com",
  "created_at": "2026-09-04T08:00:00Z"
}
```

---

### 2. Create an Invoice

Note that amounts are in integer cents ($45.00 = 4500 cents). The server automatically calculates the total ($2 \times 4500 + 1 \times 1500 = 10500$ cents = $105.00).

```bash
curl -s -X POST http://localhost:8000/api/v1/invoices \
  -H "Authorization: Bearer dodo_live_testkey1234567890abcdef1234567890" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "c1f72810-7389-4a0b-932f-b42e718b5ef1",
    "due_date": "2026-09-30",
    "auto_finalize": true,
    "line_items": [
      {
        "description": "Enterprise Cloud Hosting - September",
        "quantity": 2,
        "unit_amount_cents": 4500
      },
      {
        "description": "Dedicated IPv4 Address",
        "quantity": 1,
        "unit_amount_cents": 1500
      }
    ]
  }' | jq .
```

**Expected Response (HTTP 201 Created):**
```json
{
  "id": "inv_8a92b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
  "business_id": "b0a11223-4455-6677-8899-aabbccddeeff",
  "customer_id": "c1f72810-7389-4a0b-932f-b42e718b5ef1",
  "state": "open",
  "currency": "USD",
  "total_amount_cents": 10500,
  "due_date": "2026-09-30",
  "line_items": [
    {
      "id": "li_11111111-2222-3333-4444-555555555555",
      "description": "Enterprise Cloud Hosting - September",
      "quantity": 2,
      "unit_amount_cents": 4500,
      "total_amount_cents": 9000
    },
    {
      "id": "li_66666666-7777-8888-9999-000000000000",
      "description": "Dedicated IPv4 Address",
      "quantity": 1,
      "unit_amount_cents": 1500,
      "total_amount_cents": 1500
    }
  ],
  "created_at": "2026-09-04T08:05:00Z"
}
```

---

### 3. Attempt Payment — Success Case (`tok_success`)

Includes the mandatory `Idempotency-Key` header:

```bash
curl -s -X POST http://localhost:8000/api/v1/invoices/inv_8a92b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c/pay \
  -H "Authorization: Bearer dodo_live_testkey1234567890abcdef1234567890" \
  -H "Idempotency-Key: pay_unique_key_001" \
  -H "Content-Type: application/json" \
  -d '{
    "card_token": "tok_success"
  }' | jq .
```

**Expected Response (HTTP 200 OK):**
```json
{
  "payment_attempt_id": "pay_98765432-1234-5678-9abc-def012345678",
  "invoice_id": "inv_8a92b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
  "amount_cents": 10500,
  "currency": "USD",
  "status": "succeeded",
  "psp_reference": "psp_ref_d1a2b3c4",
  "invoice_state": "paid",
  "failure_code": null,
  "created_at": "2026-09-04T08:06:00Z"
}
```

*Invoice is now in terminal state `paid`. Repeating the request with the same `Idempotency-Key` immediately returns the identical cached response.*

---

### 4. Attempt Payment — Failure Case (`tok_insufficient_funds`)

Create another open invoice and attempt payment with an insufficient funds token:

```bash
curl -s -X POST http://localhost:8000/api/v1/invoices/inv_second_invoice_id/pay \
  -H "Authorization: Bearer dodo_live_testkey1234567890abcdef1234567890" \
  -H "Idempotency-Key: pay_unique_key_002" \
  -H "Content-Type: application/json" \
  -d '{
    "card_token": "tok_insufficient_funds"
  }' | jq .
```

**Expected Response (HTTP 402 Payment Required):**
```json
{
  "error": {
    "code": "PAYMENT_FAILED",
    "message": "Payment declined by processor: insufficient_funds",
    "payment_attempt_id": "pay_f1e2d3c4-b5a6-7890-1234-56789abcdef0",
    "invoice_id": "inv_second_invoice_id",
    "failure_code": "insufficient_funds",
    "invoice_state": "open"
  }
}
```

*Notice that the invoice remains safely in `open` state, allowing the customer to retry with an alternative card.*

---

### 5. Attempt Payment — Handled Timeout (`tok_timeout`)

The mock PSP sleeps 30 seconds. The service's internal HTTP client has a 5.0-second timeout, so it does **not** hang:

```bash
curl -s -X POST http://localhost:8000/api/v1/invoices/inv_open_id/pay \
  -H "Authorization: Bearer dodo_live_testkey1234567890abcdef1234567890" \
  -H "Idempotency-Key: pay_unique_key_003" \
  -H "Content-Type: application/json" \
  -d '{
    "card_token": "tok_timeout"
  }' | jq .
```

**Expected Response (HTTP 504 Gateway Timeout):**
```json
{
  "error": {
    "code": "PSP_TIMEOUT",
    "message": "Payment processor timed out after 5.0s. Payment attempt recorded in pending state.",
    "payment_attempt_id": "pay_timeout_id",
    "invoice_id": "inv_open_id",
    "invoice_state": "open"
  }
}
```

---

## Register Webhook Endpoint

Businesses register their endpoint to receive signed events:

```bash
curl -s -X POST http://localhost:8000/api/v1/webhooks/endpoints \
  -H "Authorization: Bearer dodo_live_testkey1234567890abcdef1234567890" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.mybusiness.com/webhooks/dodo"
  }' | jq .
```

**Response includes the signing secret:**
```json
{
  "id": "wh_sec_1234",
  "url": "https://api.mybusiness.com/webhooks/dodo",
  "secret": "whsec_98f7e6d5c4b3a210fedcba0987654321",
  "is_active": true
}
```

---

## Running the Automated Test Suite

```bash
# Inside docker container or local environment:
pytest -v tests/
```

Runs 35+ test cases verifying:
- Integer minor unit arithmetic.
- State machine transition invariants and terminal state rejection.
- Idempotency key deduplication.
- PSP token failure and timeout handling.
- HMAC-SHA256 signature verification.
