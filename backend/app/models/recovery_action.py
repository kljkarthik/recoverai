import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.recovery_workflow import RecoveryWorkflow
    from app.models.recovery_attempt import RecoveryAttempt
    from app.models.recovery_outcome import RecoveryOutcome

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("recovery_workflows.id", ondelete="CASCADE"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    ai_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    policy_result: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="recovery_actions")
    workflow: Mapped[Optional["RecoveryWorkflow"]] = relationship("RecoveryWorkflow", back_populates="actions")
    attempts: Mapped[List["RecoveryAttempt"]] = relationship("RecoveryAttempt", back_populates="recovery_action", cascade="all, delete-orphan")
    outcomes: Mapped[List["RecoveryOutcome"]] = relationship("RecoveryOutcome", back_populates="recovery_action", cascade="all, delete-orphan")
