import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.recovery_workflow import RecoveryWorkflow

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RecoveryDecision(Base):
    __tablename__ = "recovery_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("recovery_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    failure_category: Mapped[str] = mapped_column(String(50), nullable=False)
    recommended_strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    final_strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    policy_result: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("1.00"), nullable=False)
    explanation_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    workflow: Mapped["RecoveryWorkflow"] = relationship("RecoveryWorkflow", back_populates="decisions")
