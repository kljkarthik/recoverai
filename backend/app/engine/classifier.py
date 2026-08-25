from typing import Optional

class FailureClassifier:
    """Categorizes raw transaction failure reason strings into standardized failure categories."""

    TEMPORARY_DEGRADATION = "temporary_degradation"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    NETWORK_TIMEOUT = "network_timeout"
    INVALID_DETAILS = "invalid_details"
    HARD_DECLINE = "hard_decline"
    UNKNOWN_FAILURE = "unknown_failure"

    @classmethod
    def classify(cls, failure_reason: Optional[str]) -> str:
        if not failure_reason:
            return cls.UNKNOWN_FAILURE

        reason_lower = failure_reason.lower().strip()

        # Temporary Payment Degradation
        if any(term in reason_lower for term in ["gateway_timeout", "bank_processing_error", "system_busy", "temporary_bank_error", "degradation", "payment_failed", "payment_error", "bad_request_error", "razorpay_failed"]):
            return cls.TEMPORARY_DEGRADATION


        # Insufficient Funds
        if any(term in reason_lower for term in ["insufficient_funds", "low_balance", "credit_limit_exceeded", "balance_low"]):
            return cls.INSUFFICIENT_FUNDS

        # Network / Timeout Failure
        if any(term in reason_lower for term in ["network_timeout", "connection_dropped", "issuer_timeout", "timeout"]):
            return cls.NETWORK_TIMEOUT

        # Invalid Payment Details
        if any(term in reason_lower for term in ["card_expired", "expired_card", "invalid_otp", "invalid_cvv", "incorrect_pin", "invalid_card"]):
            return cls.INVALID_DETAILS

        # Hard Failure / Hard Decline
        if any(term in reason_lower for term in ["account_closed", "stolen_card", "lost_card", "fraud_block", "do_not_honor", "hard_decline"]):
            return cls.HARD_DECLINE

        # Default fallback
        return cls.UNKNOWN_FAILURE
