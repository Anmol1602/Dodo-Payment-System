# AI Usage Disclosure (AI_USAGE.md)

**Candidate:** Backend Engineering Applicant  
**Role:** Backend Engineer — Dodo Payments  
**Project:** Minimal Invoice & Payment Service  

---

## 1. Tools Used and Functional Breakdown

During the design and implementation of this service, AI tools were leveraged to accelerate boilerplate creation, optimize SQL query execution patterns, and validate edge-case behaviors:

* **Claude 3.7 Sonnet / Antigravity Agent (Code Architecture & Scaffolding):**
  * Used for drafting initial Pydantic v2 schemas, FastAPI dependency injection boilerplate, and OpenAPI 3.1 schema definitions.
  * Used to generate the OpenAPI documentation structure and preliminary async HTTP client abstractions.
* **Cursor (Autocomplete & Unit Test Scaffolding):**
  * Used for fast tab-completion across repetitive test cases (e.g., parameterized pytest tables testing valid and invalid state machine transitions).
  * Generated standard mock fixtures for HTTP client response mocking.
* **LLM Query Optimization & Execution Plan Analysis:**
  * Prompted an LLM to evaluate query plans (`EXPLAIN ANALYZE`) for high-concurrency invoice listing and state filtering. The LLM recommended compound index structures `(business_id, state, created_at DESC)` and an index on `(invoice_id, created_at DESC)` for payment attempt timelines.
* **ChatGPT (Research & Trade-off Evaluation):**
  * Used to research edge cases in PostgreSQL advisory locks (`pg_advisory_xact_lock`) versus explicit relational idempotency tables under high connection pooling contention (PgBouncer in transaction pooling mode).

---

## 2. Three Decisions Made Independently (Against or Beyond AI Proposals)

### Decision 1: Database Normalization Over AI-Suggested JSONB Line Items
* **What the AI Proposed:**  
  The AI suggested storing invoice line items as a denormalized `JSONB` array directly inside the `invoices` table (`invoices.line_items = [{"description": "...", "quantity": 2, "unit_amount_cents": 1500}]`). It argued this would allow single-query inserts without multi-table joins.
* **What I Chose:**  
  I rejected this suggestion and implemented a fully normalized `invoice_line_items` table with a foreign key referencing `invoices.id (ON DELETE RESTRICT)` and explicit typed columns (`description VARCHAR(255)`, `quantity INTEGER`, `unit_amount_cents BIGINT`).
* **Why:**  
  * **Database-Level Integrity:** A `JSONB` column cannot enforce relational check constraints like `CHECK (quantity > 0)` and `CHECK (unit_amount_cents >= 0)` without complex, fragile JSON schema triggers.
  * **Query Performance & Analytics:** Denormalized JSONB incurs deserialization and serialization CPU overhead on every invoice fetch. Normalization allows PostgreSQL's storage engine to use fixed-width integer arithmetic and optimized B-tree indexing.
  * **Auditability & Future Ledger Operations:** If line items ever need tax classification codes, SKU references, or individual line item discounts in the future, relational tables scale cleanly without rewriting entire JSON blobs.

### Decision 2: Transaction-Scoped Idempotency Records Over Postgres Advisory Locks
* **What the AI Proposed:**  
  The AI suggested using PostgreSQL session/transaction advisory locks: `SELECT pg_advisory_xact_lock(hashtext(idempotency_key))` to serialize concurrent requests sharing the same key.
* **What I Chose:**  
  I chose an explicit `idempotency_records` table with a database-level unique constraint on `(business_id, idempotency_key)`, combined with pessimistic row-locking (`SELECT ... FOR UPDATE`) on the target `invoices` row.
* **Why:**  
  * **PgBouncer & Connection Pooling Compatibility:** In production environments running connection poolers like PgBouncer in transaction mode, session-level advisory locks can leak across pooled connections or behave unpredictably upon sudden client disconnects.
  * **Hash Collision Risk:** `pg_advisory_xact_lock` relies on 32-bit or 64-bit integer hashes, creating a non-zero probability of hash collisions across different idempotency keys under high volume.
  * **Persistence of Cached Response:** An advisory lock only serializes execution; it does not store the returned HTTP status code or JSON response payload. The `idempotency_records` table acts as both a concurrency barrier (the second concurrent insert raises a unique constraint violation) and a durable cache for replaying identical responses.

### Decision 3: Decoupled Indeterminate State for PSP Timeouts Over Immediate Failure
* **What the AI Proposed:**  
  When handling `tok_timeout` (where the mock PSP takes 30 seconds to respond), the AI suggested setting a short 3-second HTTP client timeout and immediately transitioning both the `PaymentAttempt` and the `Invoice` to `payment_failed` / `open` upon hitting the `TimeoutException`.
* **What I Chose:**  
  I implemented an **indeterminate pending state** pattern:
  * When the PSP client times out (configured to 5.0 seconds), the `PaymentAttempt` is recorded in state `pending` with `failure_reason = "gateway_timeout"`.
  * The `Invoice` remains in `open` (or `processing`), rather than being marked as definitively failed.
  * The API responds with HTTP `504 Gateway Timeout` (or HTTP `202 Accepted` with a retryable payload), instructing the client that payment status is unresolved.
* **Why:**  
  In payment systems, a network timeout between the merchant service and the PSP does **not** mean the customer was not charged. The upstream card network may have authorized the transaction after the timeout occurred. Marking the payment as definitively failed would prompt the customer to retry, resulting in an inadvertent double-charge. Leaving the payment attempt in `pending` preserves the audit trail until an asynchronous reconciliation job or webhook clarifies the charge's final status.

---

## 3. What the AI Got Wrong & My Corrections

### 1. The Floating-Point Arithmetic Flaw & Normalization Oversight
* **The Error:**  
  During the initial code generation phase, the AI generated a total calculation function using standard Python floating-point types:
  ```python
  # AI-generated flaw:
  total = sum(item["quantity"] * (item["unit_amount"] / 100.0) for item in items)
  invoice.total_amount = round(total, 2)
  ```
  Additionally, the AI omitted composite index definitions on frequently filtered tenant dimensions, leading to sequential scans on `invoices WHERE business_id = ? AND state = ?`.
* **My Correction:**  
  1. **Strict Integer Minor Units (Cents):** I eradicated all floating-point numbers across the entire payment and calculation path. All line item amounts and invoice totals are stored and computed strictly as minor integer units (`BIGINT` cents). The server calculation guarantees:
     $$\text{total\_amount\_cents} = \sum (\text{quantity} \times \text{unit\_amount\_cents})$$
     with integer overflow checks and strict positive boundary assertions.
  2. **Relational Schema Normalization:** I restructured the AI's naive single-table draft into an optimized 3NF relational schema. Specifically, I extracted line items into `invoice_line_items`, indexed `(business_id, state)` and `(business_id, created_at DESC)`, and established composite unique constraints on `(business_id, idempotency_key)` to prevent cross-tenant key pollution.
  3. **Terminal State Invariants:** The AI's state machine initially allowed an invoice in the `paid` state to be reopened if a subsequent payment attempt was submitted with a declining card token. I corrected the state machine guards so that `paid` and `void` are strictly terminal states: any payment request against an invoice in `paid`, `void`, or `uncollectible` is rejected at the API boundary with a descriptive `409 Conflict` error.

---

## Summary of Verification
Every component was independently verified using an automated `pytest` suite comprising 35+ test cases:
* Tested integer precision edge cases (large values, zero unit amounts, positive integer enforcement).
* Simulated concurrent payment requests with identical `Idempotency-Key` headers.
* Verified HMAC-SHA256 signature verification on mock webhook receivers.
* Verified that slow PSP calls (`tok_timeout`) do not hang the FastAPI worker and do not corrupt invoice state.
