import uuid
from datetime import datetime, timezone
from typing import Optional, Any, Dict, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction
    from app.models.recovery_workflow import RecoveryWorkflow

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("recovery_workflows.id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    decision: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status_result: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    transaction: Mapped[Optional["Transaction"]] = relationship("Transaction", back_populates="audit_logs")
    workflow: Mapped[Optional["RecoveryWorkflow"]] = relationship("RecoveryWorkflow", back_populates="audit_logs")
