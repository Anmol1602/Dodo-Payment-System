import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Index, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    secret: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="webhook_endpoints")
    deliveries = relationship("WebhookDelivery", back_populates="endpoint", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint_id: Mapped[str] = mapped_column(String(36), ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")  # pending, delivered, failed
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_status_code: Mapped[int] = mapped_column(Integer, nullable=True)
    last_error: Mapped[str] = mapped_column(Text, nullable=True)
    next_retry_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    endpoint = relationship("WebhookEndpoint", back_populates="deliveries")

    __table_args__ = (
        Index("idx_webhook_deliveries_pending", "status", "next_retry_at"),
    )
