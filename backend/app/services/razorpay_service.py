import razorpay
from typing import Optional, Dict, Any
from app.core.config import settings

class RazorpayConfigError(Exception):
    """Raised when Razorpay credentials are missing or unconfigured."""
    pass

class RazorpayVerificationError(Exception):
    """Raised when Razorpay payment signature verification fails."""
    pass

class RazorpayService:
    """Framework-independent service wrapper for Razorpay Test Mode interactions."""

    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None):
        self._key_id = key_id
        self._key_secret = key_secret

    @property
    def key_id(self) -> Optional[str]:
        if self._key_id is not None:
            return self._key_id
        return settings.RAZORPAY_KEY_ID

    @property
    def key_secret(self) -> Optional[str]:
        if self._key_secret is not None:
            return self._key_secret
        return settings.RAZORPAY_KEY_SECRET

    def get_client(self) -> razorpay.Client:
        k_id = self.key_id
        k_secret = self.key_secret

        if not k_id or not k_secret:
            raise RazorpayConfigError(
                "Razorpay Test Mode credentials are not configured. "
                "Please ensure RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET environment variables are set."
            )
        return razorpay.Client(auth=(k_id, k_secret))

    def create_order(
        self, amount_inr: float, currency: str = "INR", receipt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates a Razorpay order converting INR to paise.
        Returns safe data containing order_id, amount, currency, and key_id.
        Secret is NEVER returned or exposed.
        """
        if amount_inr <= 0:
            raise ValueError("Order amount must be greater than zero.")

        client = self.get_client()
        amount_paise = int(round(amount_inr * 100))

        order_data: Dict[str, Any] = {
            "amount": amount_paise,
            "currency": currency,
            "payment_capture": 1
        }
        if receipt:
            order_data["receipt"] = receipt

        order = client.order.create(data=order_data)

        return {
            "order_id": order["id"],
            "amount": amount_inr,
            "amount_paise": amount_paise,
            "currency": order.get("currency", currency),
            "key_id": self.key_id
        }

    def verify_payment_signature(
        self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str
    ) -> bool:
        """Verifies Razorpay payment signature server-side using SDK utility."""
        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            raise ValueError("Missing required payment verification parameters.")

        client = self.get_client()
        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)
            return True
        except Exception as e:
            raise RazorpayVerificationError(f"Razorpay signature verification failed: {str(e)}")

razorpay_service = RazorpayService()
