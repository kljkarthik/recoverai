from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from app.core.config import settings
from app.models.transaction import Transaction
from app.models.recovery_workflow import RecoveryWorkflow
from app.engine.classifier import FailureClassifier

class PolicyEvaluationResult(BaseModel):
    allowed: bool = Field(..., description="Whether the recommended strategy is allowed by safety policy")
    policy_result: str = Field(..., description="ALLOWED, BLOCKED, or ESCALATED")
    final_strategy: str = Field(..., description="The final strategy permitted by policy rules")
    reason: str = Field(..., description="Reason for policy evaluation outcome")

class PolicyEngine:
    """Deterministic Safety and Policy Guardrail Engine.
    
    Ensures that no AI or rule recommendation can bypass configurable safety limits.
    """

    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    ESCALATED = "ESCALATED"

    @classmethod
    def evaluate(
        cls,
        recommended_strategy: str,
        transaction: Transaction,
        workflow: RecoveryWorkflow,
        attempt_count: int = 0
    ) -> PolicyEvaluationResult:
        tx_amount = float(transaction.amount) if isinstance(transaction.amount, (Decimal, float, int)) else 0.0

        # Guardrail 1: Hard Decline Blocking
        if workflow.failure_category == FailureClassifier.HARD_DECLINE:
            return PolicyEvaluationResult(
                allowed=False,
                policy_result=cls.BLOCKED,
                final_strategy="NO_ACTION",
                reason="Policy Block: Retries and outreach strictly forbidden for hard decline payment failures."
            )

        # Guardrail 2: Retry Limit Enforcement
        if recommended_strategy == "RETRY" and attempt_count >= settings.MAX_RETRY_ATTEMPTS:
            return PolicyEvaluationResult(
                allowed=False,
                policy_result=cls.BLOCKED,
                final_strategy="NO_ACTION",
                reason=f"Policy Block: Maximum retry attempt limit ({settings.MAX_RETRY_ATTEMPTS}) reached for workflow."
            )

        # Guardrail 3: High Value Escalation Override
        if tx_amount >= settings.HIGH_VALUE_THRESHOLD and recommended_strategy != "ESCALATE":
            return PolicyEvaluationResult(
                allowed=False,
                policy_result=cls.ESCALATED,
                final_strategy="ESCALATE",
                reason=f"Policy Escalation: Transaction amount (₹{tx_amount:,.2f}) exceeds high-value threshold (₹{settings.HIGH_VALUE_THRESHOLD:,.2f}). Forced manual escalation."
            )

        # Guardrail 4: Default Approval for Allowed Strategies
        return PolicyEvaluationResult(
            allowed=True,
            policy_result=cls.ALLOWED,
            final_strategy=recommended_strategy,
            reason="Policy Approved: Action complies with all safety rules, attempt limits, and monetary thresholds."
        )
