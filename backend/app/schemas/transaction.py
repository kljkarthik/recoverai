from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class HealthCheckResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    database: str = Field(..., json_schema_extra={"example": "connected"})
    timestamp: datetime

class TransactionBase(BaseModel):
    customer_id: str = Field(..., description="ID of the customer making the transaction")
    amount: Decimal = Field(..., gt=0, description="Monetary transaction amount")
    currency: str = Field(default="INR", max_length=10, description="ISO Currency Code")
    status: str = Field(..., description="Transaction status e.g. failed, success, pending, abandoned")
    failure_reason: Optional[str] = Field(default=None, description="Reason for failure if status is failed")
    payment_method: str = Field(..., description="Payment method used e.g. card, upi, netbanking")
    attempt_number: int = Field(default=1, ge=1, description="Attempt sequence count")

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    lifetime_value: Decimal
    risk_score: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
