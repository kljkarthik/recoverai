import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.recovery_action import RecoveryAction

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RecoveryOutcome(Base):
    __tablename__ = "recovery_outcomes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recovery_action_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_actions.id", ondelete="CASCADE"), nullable=False, index=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    amount_recovered: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    recovery_action: Mapped["RecoveryAction"] = relationship("RecoveryAction", back_populates="outcomes")
