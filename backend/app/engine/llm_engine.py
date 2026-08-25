import logging
import concurrent.futures
from typing import Optional, Dict, Any
from decimal import Decimal
from app.core.config import settings
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.engine.base import BaseDecisionEngine, StrategyRecommendation
from app.engine.rule_engine import RuleBasedDecisionEngine
from app.engine.providers import BaseLLMProvider, MockLLMProvider, OpenAILLMProvider, LLMRecommendationSchema

logger = logging.getLogger(__name__)

class LLMDecisionEngine(BaseDecisionEngine):
    """AI/LLM-based decision engine implementing BaseDecisionEngine.
    
    Acts as an explainable recommendation layer with safe, transparent fallback to RuleBasedDecisionEngine.
    """

    ALLOWED_STRATEGIES = {"RETRY", "NOTIFY_CUSTOMER", "ESCALATE", "NO_ACTION"}

    def __init__(self, provider: Optional[BaseLLMProvider] = None, fallback_engine: Optional[BaseDecisionEngine] = None):
        self.fallback_engine = fallback_engine or RuleBasedDecisionEngine()
        if provider:
            self.provider = provider
        else:
            provider_type = settings.LLM_PROVIDER.lower()
            if provider_type == "openai":
                self.provider = OpenAILLMProvider()
            else:
                self.provider = MockLLMProvider()

    def _build_anonymized_prompt(
        self,
        transaction: Transaction,
        failure_category: str,
        customer: Optional[Customer] = None
    ) -> str:
        tx_amount = float(transaction.amount) if isinstance(transaction.amount, (Decimal, float, int)) else 0.0

        # Anonymized telemetry without customer PII (no names, emails, phones)
        cust_telemetry = {}
        if customer:
            cust_telemetry = {
                "total_transactions": customer.total_transactions,
                "successful_transactions": customer.successful_transactions,
                "failed_transactions": customer.failed_transactions,
                "lifetime_value_inr": float(customer.lifetime_value) if isinstance(customer.lifetime_value, (Decimal, float, int)) else 0.0,
                "risk_score": float(customer.risk_score) if isinstance(customer.risk_score, (Decimal, float, int)) else 0.0,
            }

        prompt = f"""
ANONYMIZED PAYMENT FAILURE TELEMETRY:
- Transaction Amount (INR): {tx_amount:.2f}
- Currency: {transaction.currency}
- Raw Failure Reason: {transaction.failure_reason or 'None'}
- Ingestion Failure Category: {failure_category}
- Payment Method: {transaction.payment_method}
- Payment Attempt Count: {transaction.attempt_number}
- Customer Telemetry (PII Scrubbed): {cust_telemetry}

SYSTEM GUARDRAILS REFERENCE:
- High Value Escalation Threshold: ₹{settings.HIGH_VALUE_THRESHOLD:,.2f}
- Maximum Allowed Retries: {settings.MAX_RETRY_ATTEMPTS}

RECOMMENDATION TASK:
Analyze the telemetry above and select the optimal recovery strategy: RETRY, NOTIFY_CUSTOMER, ESCALATE, or NO_ACTION.
Provide a clear explainable reason, confidence score (0.0 to 1.0), key risk factor, and suggested delay.
"""
        return prompt.strip()

    def _execute_with_timeout(self, prompt: str) -> LLMRecommendationSchema:
        timeout_seconds = settings.LLM_TIMEOUT_SECONDS

        # Run provider call in a thread pool to enforce strict timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.provider.generate_recommendation, prompt)
            try:
                return future.result(timeout=timeout_seconds)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"LLM provider call timed out after {timeout_seconds} seconds.")

    def recommend_strategy(
        self,
        transaction: Transaction,
        failure_category: str,
        customer: Optional[Customer] = None
    ) -> StrategyRecommendation:
        prompt = self._build_anonymized_prompt(transaction, failure_category, customer)

        try:
            # 1. Execute LLM call with strict timeout
            llm_res: LLMRecommendationSchema = self._execute_with_timeout(prompt)

            # 2. Strategy Enum Validation
            strategy = llm_res.recommended_strategy
            if strategy not in self.ALLOWED_STRATEGIES:
                raise ValueError(f"LLM returned invalid strategy '{strategy}'. Must be one of {self.ALLOWED_STRATEGIES}.")

            # 3. Confidence Threshold Check
            if llm_res.confidence_score < settings.LLM_MIN_CONFIDENCE:
                raise ValueError(
                    f"LLM confidence score ({llm_res.confidence_score:.2f}) is below minimum threshold ({settings.LLM_MIN_CONFIDENCE:.2f})."
                )

            # Valid AI Recommendation
            return StrategyRecommendation(
                recommended_strategy=strategy,
                reason=llm_res.reason,
                confidence_score=llm_res.confidence_score,
                explanation_details={
                    "engine_type": "llm",
                    "provider": settings.LLM_PROVIDER,
                    "model_name": settings.LLM_MODEL_NAME,
                    "fallback_used": False,
                    "primary_risk_factor": llm_res.primary_risk_factor,
                    "recommended_delay_hours": llm_res.recommended_delay_hours,
                    "ai_confidence": llm_res.confidence_score,
                    "ai_reasoning": llm_res.reason
                }
            )

        except Exception as err:
            logger.warning(f"LLM Decision Engine failure or low confidence: {err}. Executing safe fallback to RuleBasedDecisionEngine.")

            # Safe Fallback to RuleBasedDecisionEngine
            rule_rec = self.fallback_engine.recommend_strategy(transaction, failure_category, customer)

            # Augment explanation details with fallback audit telemetry
            fallback_details = dict(rule_rec.explanation_details or {})
            fallback_details.update({
                "engine_type": "llm_fallback",
                "fallback_used": True,
                "fallback_reason": str(err),
                "fallback_rule_strategy": rule_rec.recommended_strategy,
                "provider": settings.LLM_PROVIDER
            })

            return StrategyRecommendation(
                recommended_strategy=rule_rec.recommended_strategy,
                reason=f"LLM Fallback ({str(err)}): {rule_rec.reason}",
                confidence_score=rule_rec.confidence_score,
                explanation_details=fallback_details
            )
