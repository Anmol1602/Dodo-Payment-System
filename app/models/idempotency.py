import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_path: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    # Use generic JSON which translates to JSONB on PostgreSQL and JSON/Text on SQLite
    response_body = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("business_id", "idempotency_key", name="uq_business_idempotency_key"),
        Index("idx_idempotency_lookup", "business_id", "idempotency_key"),
    )
