"""Initial schema migration for Dodo Invoicing & Payment Service

Revision ID: 001_initial
Revises: None
Create Date: 2026-09-04 08:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. businesses
    op.create_table(
        "businesses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 2. api_keys
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("business_id", sa.String(36), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_prefix", sa.String(16), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("label", sa.String(100), nullable=False, server_default="Default Key"),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_api_keys_active", "api_keys", ["key_hash", "is_revoked"])

    # 3. customers
    op.create_table(
        "customers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("business_id", sa.String(36), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_customers_business_created", "customers", ["business_id", "created_at"])

    # 4. invoices
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("business_id", sa.String(36), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("state", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("total_amount_cents", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("total_amount_cents >= 0", name="chk_invoice_total_positive"),
    )
    op.create_index("idx_invoices_business_state", "invoices", ["business_id", "state"])
    op.create_index("idx_invoices_business_created", "invoices", ["business_id", "created_at"])

    # 5. invoice_line_items
    op.create_table(
        "invoice_line_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("total_amount_cents", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="chk_line_item_quantity_positive"),
        sa.CheckConstraint("unit_amount_cents >= 0", name="chk_line_item_unit_amount_positive"),
        sa.CheckConstraint("total_amount_cents >= 0", name="chk_line_item_total_positive"),
    )
    op.create_index("idx_line_items_invoice", "invoice_line_items", ["invoice_id"])

    # 6. payment_attempts
    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("business_id", sa.String(36), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("card_token", sa.String(128), nullable=False),
        sa.Column("psp_reference", sa.String(128), nullable=True),
        sa.Column("failure_code", sa.String(64), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount_cents > 0", name="chk_payment_amount_positive"),
    )
    op.create_index("idx_payments_invoice_created", "payment_attempts", ["invoice_id", "created_at"])

    # 7. idempotency_records
    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("business_id", sa.String(36), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("request_path", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("business_id", "idempotency_key", name="uq_business_idempotency_key"),
    )
    op.create_index("idx_idempotency_lookup", "idempotency_records", ["business_id", "idempotency_key"])

    # 8. webhook_endpoints
    op.create_table(
        "webhook_endpoints",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("business_id", sa.String(36), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("secret", sa.String(64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 9. webhook_deliveries
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("endpoint_id", sa.String(36), sa.ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_webhook_deliveries_pending", "webhook_deliveries", ["status", "next_retry_at"])


def downgrade() -> None:
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_endpoints")
    op.drop_table("idempotency_records")
    op.drop_table("payment_attempts")
    op.drop_table("invoice_line_items")
    op.drop_table("invoices")
    op.drop_table("customers")
    op.drop_table("api_keys")
    op.drop_table("businesses")
