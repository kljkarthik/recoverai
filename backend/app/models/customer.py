import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.transaction import Transaction

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    total_transactions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_transactions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_transactions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lifetime_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.00"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
