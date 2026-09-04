import uuid
from datetime import datetime, date
from sqlalchemy import String, BigInteger, Integer, Date, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    total_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="invoices")
    customer = relationship("Customer", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin")
    payment_attempts = relationship("PaymentAttempt", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin", order_by="desc(PaymentAttempt.created_at)")

    __table_args__ = (
        CheckConstraint("total_amount_cents >= 0", name="chk_invoice_total_positive"),
        Index("idx_invoices_business_state", "business_id", "state"),
        Index("idx_invoices_business_created", "business_id", "created_at"),
    )


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_line_item_quantity_positive"),
        CheckConstraint("unit_amount_cents >= 0", name="chk_line_item_unit_amount_positive"),
        CheckConstraint("total_amount_cents >= 0", name="chk_line_item_total_positive"),
    )
