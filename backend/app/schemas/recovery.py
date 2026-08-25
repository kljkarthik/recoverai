from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class WorkflowCreate(BaseModel):
    transaction_id: str = Field(..., description="UUID of the failed transaction")
    max_retries: Optional[int] = Field(default=None, ge=1, le=10, description="Override maximum retries")

class DecisionResponse(BaseModel):
    id: str
    workflow_id: str
    failure_category: str
    recommended_strategy: str
    final_strategy: str
    reason: str
    policy_result: str
    confidence_score: Decimal
    explanation_details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AttemptCreate(BaseModel):
    success: bool = Field(..., description="Whether the simulated recovery attempt succeeded")
    amount_recovered: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0, description="Amount recovered if successful")
    response_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata from simulated gateway/messaging response")

class AttemptResponse(BaseModel):
    id: str
    recovery_action_id: str
    workflow_id: str
    attempt_number: int
    status: str
    success: bool
    amount_recovered: Decimal
    response_metadata: Optional[Dict[str, Any]] = None
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ActionResponse(BaseModel):
    id: str
    transaction_id: str
    workflow_id: Optional[str] = None
    action_type: str
    reason: str
    ai_confidence: Optional[Decimal] = None
    policy_result: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WorkflowResponse(BaseModel):
    id: str
    transaction_id: str
    status: str
    failure_category: str
    current_step: int
    max_retries: int
    next_retry_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    decisions: List[DecisionResponse] = []
    actions: List[ActionResponse] = []
    attempts: List[AttemptResponse] = []

    model_config = ConfigDict(from_attributes=True)

class RecoveryMetricsResponse(BaseModel):
    revenue_at_risk: Decimal = Field(..., description="Total value across all failed/abandoned transactions")
    recovery_attempts: int = Field(..., description="Total recovery execution attempts")
    successful_recoveries: int = Field(..., description="Total successful recovery attempts")
    recovery_rate: float = Field(..., description="Percentage of successful recoveries over total failed transactions")
    revenue_recovered: Decimal = Field(..., description="Net total revenue successfully recovered")
    total_failed_transactions: int = Field(..., description="Count of failed/abandoned transactions")

    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: str
    workflow_id: Optional[str] = None
    transaction_id: Optional[str] = None
    event_type: str
    actor: str
    decision: str
    action: Optional[str] = None
    reason: str
    status_result: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
