import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.recovery_action import RecoveryAction
    from app.models.recovery_workflow import RecoveryWorkflow

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recovery_action_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_actions.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    amount_recovered: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    response_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    recovery_action: Mapped["RecoveryAction"] = relationship("RecoveryAction", back_populates="attempts")
    workflow: Mapped["RecoveryWorkflow"] = relationship("RecoveryWorkflow", back_populates="attempts")
