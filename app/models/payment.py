import uuid
from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, Index, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False, index=True)
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")  # pending, succeeded, failed
    card_token: Mapped[str] = mapped_column(String(128), nullable=False)
    psp_reference: Mapped[str] = mapped_column(String(128), nullable=True)
    failure_code: Mapped[str] = mapped_column(String(64), nullable=True)
    failure_message: Mapped[str] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="payment_attempts")

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="chk_payment_amount_positive"),
        Index("idx_payments_invoice_created", "invoice_id", "created_at"),
    )
