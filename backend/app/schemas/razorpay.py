from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class RazorpayOrderCreate(BaseModel):
    amount: float = Field(..., gt=0, description="Amount in INR (e.g. 1499.00)")
    currency: str = Field(default="INR", description="Currency code (default INR)")
    receipt: Optional[str] = Field(default=None, description="Optional receipt identifier")

class RazorpayOrderResponse(BaseModel):
    order_id: str
    amount: float
    amount_paise: int
    currency: str
    key_id: str

class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str = Field(..., description="Razorpay Order ID")
    razorpay_payment_id: str = Field(..., description="Razorpay Payment ID")
    razorpay_signature: str = Field(..., description="Razorpay HMAC SHA256 Signature")

class RazorpayVerifyResponse(BaseModel):
    status: str
    verified: bool
    razorpay_order_id: str
    razorpay_payment_id: str
    message: str

class RazorpayFailureRequest(BaseModel):
    razorpay_order_id: Optional[str] = Field(default=None)
    razorpay_payment_id: Optional[str] = Field(default=None)
    error_code: Optional[str] = Field(default="BAD_REQUEST_ERROR")
    error_description: Optional[str] = Field(default="Payment failed during Razorpay checkout")
    error_reason: Optional[str] = Field(default="gateway_timeout")
    amount: float = Field(default=1499.00, gt=0)
    payment_method: Optional[str] = Field(default="razorpay")

class RazorpayFailureResponse(BaseModel):
    status: str
    transaction_id: str
    workflow_id: str
    failure_category: str
    recommended_strategy: str
    final_strategy: str
    policy_result: str
    ai_confidence: float
    ai_reasoning: str
    attempt_recorded: bool
    attempt_success: Optional[bool] = None
    amount_recovered: float = 0.0
