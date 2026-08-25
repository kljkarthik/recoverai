import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.recovery_workflow import RecoveryWorkflow
    from app.models.recovery_action import RecoveryAction
    from app.models.audit_log import AuditLog

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="transactions")
    recovery_workflows: Mapped[List["RecoveryWorkflow"]] = relationship("RecoveryWorkflow", back_populates="transaction", cascade="all, delete-orphan")
    recovery_actions: Mapped[List["RecoveryAction"]] = relationship("RecoveryAction", back_populates="transaction", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="transaction", cascade="all, delete-orphan")
