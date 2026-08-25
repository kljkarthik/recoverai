import time
from typing import Optional, Dict, Any
from app.engine.providers.base_provider import BaseLLMProvider, LLMRecommendationSchema

class MockLLMProvider(BaseLLMProvider):
    """Deterministic Mock LLM Provider for offline testing and development.
    
    Supports simulated scenarios: 'VALID', 'TIMEOUT', 'PROVIDER_ERROR', 'MALFORMED', 'INVALID_STRATEGY', 'LOW_CONFIDENCE'.
    """

    VALID = "VALID"
    TIMEOUT = "TIMEOUT"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    MALFORMED = "MALFORMED"
    INVALID_STRATEGY = "INVALID_STRATEGY"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"

    def __init__(self, mode: str = "VALID", default_delay: float = 0.0):
        self.mode = mode
        self.default_delay = default_delay

    def generate_recommendation(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> LLMRecommendationSchema:
        if self.default_delay > 0:
            time.sleep(self.default_delay)

        if self.mode == self.TIMEOUT:
            raise TimeoutError("Mock LLM Provider call timed out after 5.0 seconds.")

        if self.mode == self.PROVIDER_ERROR:
            raise RuntimeError("Mock LLM Provider API connection failed (503 Service Unavailable).")

        if self.mode == self.MALFORMED:
            raise ValueError("Malformed response from Mock LLM Provider: JSONDecodeError at line 1 column 1.")

        if self.mode == self.INVALID_STRATEGY:
            # We return a model instance with invalid strategy by overriding validation if needed or raising ValueError
            raise ValueError("LLM generated invalid strategy 'UNRESTRICTED_REFUND' not allowed by schema.")

        if self.mode == self.LOW_CONFIDENCE:
            return LLMRecommendationSchema(
                recommended_strategy="RETRY",
                reason="Uncertain AI recommendation due to low telemetry signals.",
                confidence_score=0.35,
                primary_risk_factor="Low telemetry confidence",
                recommended_delay_hours=12
            )

        # Dynamic fallback matching prompt context for default VALID mode
        prompt_lower = prompt.lower()

        if "temporary_degradation" in prompt_lower or "gateway_timeout" in prompt_lower or "network_timeout" in prompt_lower:
            return LLMRecommendationSchema(
                recommended_strategy="RETRY",
                reason="AI Agent analysis indicates transient network degradation; scheduling automated retry.",
                confidence_score=0.94,
                primary_risk_factor="Transient gateway network timeout",
                recommended_delay_hours=4
            )
        elif "insufficient_funds" in prompt_lower:
            return LLMRecommendationSchema(
                recommended_strategy="NOTIFY_CUSTOMER",
                reason="AI Agent detected insufficient funds pattern; recommending customer notification to top up account.",
                confidence_score=0.92,
                primary_risk_factor="Temporary account balance depletion",
                recommended_delay_hours=24
            )
        elif "invalid_details" in prompt_lower or "card_expired" in prompt_lower:
            return LLMRecommendationSchema(
                recommended_strategy="NOTIFY_CUSTOMER",
                reason="AI Agent identified expired payment credentials; recommending update link outreach.",
                confidence_score=0.95,
                primary_risk_factor="Expired payment details",
                recommended_delay_hours=0
            )
        elif "hard_decline" in prompt_lower or "stolen" in prompt_lower:
            return LLMRecommendationSchema(
                recommended_strategy="NO_ACTION",
                reason="AI Agent detected hard decline pattern; recommending no automated retries to prevent fees.",
                confidence_score=0.98,
                primary_risk_factor="Hard decline risk",
                recommended_delay_hours=0
            )

        # Default standard recommendation for temporary degradation / retryable errors
        return LLMRecommendationSchema(
            recommended_strategy="RETRY",
            reason="AI Agent analysis indicates transient network degradation; scheduling automated retry.",
            confidence_score=0.94,
            primary_risk_factor="Transient gateway network timeout",
            recommended_delay_hours=4
        )
