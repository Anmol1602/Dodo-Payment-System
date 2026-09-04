import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    api_keys = relationship("ApiKey", back_populates="business", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="business", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="business", cascade="all, delete-orphan")
    webhook_endpoints = relationship("WebhookEndpoint", back_populates="business", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False, default="Default Key")
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    business = relationship("Business", back_populates="api_keys")

    __table_args__ = (
        Index("idx_api_keys_active", "key_hash", "is_revoked"),
    )
