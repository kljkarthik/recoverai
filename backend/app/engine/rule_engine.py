from typing import Optional
from decimal import Decimal
from app.core.config import settings
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.engine.base import BaseDecisionEngine, StrategyRecommendation
from app.engine.classifier import FailureClassifier

class RuleBasedDecisionEngine(BaseDecisionEngine):
    """Deterministic, rule-based decision engine for Phase 2."""

    RETRY = "RETRY"
    NOTIFY_CUSTOMER = "NOTIFY_CUSTOMER"
    ESCALATE = "ESCALATE"
    NO_ACTION = "NO_ACTION"

    def recommend_strategy(
        self,
        transaction: Transaction,
        failure_category: str,
        customer: Optional[Customer] = None
    ) -> StrategyRecommendation:
        tx_amount = float(transaction.amount) if isinstance(transaction.amount, (Decimal, float, int)) else 0.0

        # Rule 1: High-value transaction threshold check
        if tx_amount >= settings.HIGH_VALUE_THRESHOLD:
            return StrategyRecommendation(
                recommended_strategy=self.ESCALATE,
                reason=f"Transaction amount (₹{tx_amount:,.2f}) meets or exceeds high-value escalation threshold (₹{settings.HIGH_VALUE_THRESHOLD:,.2f}).",
                confidence_score=1.0,
                explanation_details={
                    "rule_triggered": "high_value_escalation",
                    "amount": tx_amount,
                    "threshold": settings.HIGH_VALUE_THRESHOLD
                }
            )

        # Rule 2: Category-based decision rules
        if failure_category in [FailureClassifier.TEMPORARY_DEGRADATION, FailureClassifier.NETWORK_TIMEOUT]:
            return StrategyRecommendation(
                recommended_strategy=self.RETRY,
                reason=f"Failure category '{failure_category}' indicates a temporary network or processing failure eligible for automated retry.",
                confidence_score=1.0,
                explanation_details={
                    "rule_triggered": "temporary_failure_retry",
                    "category": failure_category
                }
            )

        if failure_category == FailureClassifier.INSUFFICIENT_FUNDS:
            return StrategyRecommendation(
                recommended_strategy=self.NOTIFY_CUSTOMER,
                reason="Failure categorized as insufficient funds; customer notification scheduled to prompt account re-funding or alternate payment method.",
                confidence_score=0.9,
                explanation_details={
                    "rule_triggered": "insufficient_funds_notify",
                    "category": failure_category
                }
            )

        if failure_category == FailureClassifier.INVALID_DETAILS:
            return StrategyRecommendation(
                recommended_strategy=self.NOTIFY_CUSTOMER,
                reason="Payment details invalid or expired; customer notification dispatched to request payment information update.",
                confidence_score=0.95,
                explanation_details={
                    "rule_triggered": "invalid_details_notify",
                    "category": failure_category
                }
            )

        if failure_category == FailureClassifier.HARD_DECLINE:
            return StrategyRecommendation(
                recommended_strategy=self.NO_ACTION,
                reason="Failure classified as hard decline (e.g. account closed, card stolen); automatic retries blocked to prevent fee penalties.",
                confidence_score=1.0,
                explanation_details={
                    "rule_triggered": "hard_decline_block",
                    "category": failure_category
                }
            )

        # Rule 3: Unknown / Uncertain failure fallback
        return StrategyRecommendation(
            recommended_strategy=self.ESCALATE,
            reason=f"Failure reason '{transaction.failure_reason}' categorized as unknown/uncertain; escalating for manual intervention.",
            confidence_score=0.5,
            explanation_details={
                "rule_triggered": "uncertain_failure_escalate",
                "raw_reason": transaction.failure_reason
            }
        )
