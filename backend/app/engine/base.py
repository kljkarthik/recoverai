from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.transaction import Transaction
from app.models.customer import Customer

class StrategyRecommendation(BaseModel):
    recommended_strategy: str = Field(..., description="Recommended strategy: RETRY, NOTIFY_CUSTOMER, ESCALATE, NO_ACTION")
    reason: str = Field(..., description="Explainable human-readable rationale")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score from decision engine")
    explanation_details: Dict[str, Any] = Field(default_factory=dict, description="Structured explanation payload for LLM/Rule engine inspection")

class BaseDecisionEngine(ABC):
    """Abstract interface for recovery decision engines.
    
    This interface ensures that rule-based engines (Phase 2) and LLM-based engines (Phase 3+)
    can be swapped without modifying database schemas or safety policies.
    """

    @abstractmethod
    def recommend_strategy(
        self,
        transaction: Transaction,
        failure_category: str,
        customer: Optional[Customer] = None
    ) -> StrategyRecommendation:
        """Returns a structured, explainable strategy recommendation for a given failed transaction."""
        pass
