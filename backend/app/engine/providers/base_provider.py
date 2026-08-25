from abc import ABC, abstractmethod
from typing import Literal, Optional
from pydantic import BaseModel, Field

class LLMRecommendationSchema(BaseModel):
    """Strict Pydantic schema for structured output validation from LLM decision engines."""
    recommended_strategy: Literal["RETRY", "NOTIFY_CUSTOMER", "ESCALATE", "NO_ACTION"] = Field(
        ..., description="Recommended strategy: RETRY, NOTIFY_CUSTOMER, ESCALATE, NO_ACTION"
    )
    reason: str = Field(..., min_length=5, description="Detailed human-readable rationale for the recommended strategy")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0")
    primary_risk_factor: str = Field(..., description="Key risk factor identified in payment failure telemetry")
    recommended_delay_hours: int = Field(default=0, ge=0, description="Suggested delay in hours before executing recovery action")

class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers (Mock, OpenAI, etc.)."""

    @abstractmethod
    def generate_recommendation(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> LLMRecommendationSchema:
        """Generates a structured recommendation conforming to LLMRecommendationSchema."""
        pass
