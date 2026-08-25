import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.recovery_decision import RecoveryDecision
    from app.models.recovery_action import RecoveryAction
    from app.models.recovery_attempt import RecoveryAttempt
    from app.models.audit_log import AuditLog

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RecoveryWorkflow(Base):
    __tablename__ = "recovery_workflows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str] = mapped_column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="INITIATED", nullable=False, index=True)
    failure_category: Mapped[str] = mapped_column(String(50), default="unknown_failure", nullable=False, index=True)
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    transaction: Mapped["Transaction"] = relationship("Transaction", back_populates="recovery_workflows")
    decisions: Mapped[List["RecoveryDecision"]] = relationship("RecoveryDecision", back_populates="workflow", cascade="all, delete-orphan")
    actions: Mapped[List["RecoveryAction"]] = relationship("RecoveryAction", back_populates="workflow", cascade="all, delete-orphan")
    attempts: Mapped[List["RecoveryAttempt"]] = relationship("RecoveryAttempt", back_populates="workflow", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="workflow", cascade="all, delete-orphan")
