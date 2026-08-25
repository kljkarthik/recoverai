import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.razorpay_service import RazorpayService, RazorpayConfigError, RazorpayVerificationError

client = TestClient(app)

def test_razorpay_missing_credentials():
    """Test that missing credentials raise RazorpayConfigError and returns 500 error."""
    service = RazorpayService(key_id="", key_secret="")
    with pytest.raises(RazorpayConfigError):
        service.get_client()

    with patch("app.api.routes.razorpay.razorpay_service.get_client", side_effect=RazorpayConfigError("Credentials missing")):
        response = client.post("/api/v1/razorpay/orders", json={"amount": 1499.00, "currency": "INR"})
        assert response.status_code == 500
        assert "Credentials missing" in response.json()["detail"]

def test_razorpay_order_creation_success():
    """Test successful order creation with correct paise conversion and safe response."""
    mock_order = {"id": "order_mock123", "amount": 149900, "currency": "INR"}
    
    with patch("app.services.razorpay_service.settings.RAZORPAY_KEY_ID", "rzp_test_mock_key"), \
         patch("app.services.razorpay_service.settings.RAZORPAY_KEY_SECRET", "mock_secret_key"), \
         patch("razorpay.Client") as MockClient:
        
        mock_instance = MockClient.return_value
        mock_instance.order.create.return_value = mock_order

        response = client.post(
            "/api/v1/razorpay/orders",
            json={"amount": 1499.00, "currency": "INR", "receipt": "rcpt_001"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["order_id"] == "order_mock123"
        assert data["amount"] == 1499.00
        assert data["amount_paise"] == 149900
        assert data["currency"] == "INR"
        assert data["key_id"] == "rzp_test_mock_key"
        
        # Security Assertion: Secret key is NEVER returned in response
        assert "key_secret" not in data
        assert "mock_secret_key" not in str(data)

def test_razorpay_order_invalid_amount():
    """Test rejection of invalid/zero order amounts."""
    with patch("app.services.razorpay_service.settings.RAZORPAY_KEY_ID", "rzp_test_mock_key"), \
         patch("app.services.razorpay_service.settings.RAZORPAY_KEY_SECRET", "mock_secret_key"):
        
        response = client.post("/api/v1/razorpay/orders", json={"amount": -50.00})
        assert response.status_code == 422  # Pydantic validation error gt=0

def test_razorpay_verify_signature_success():
    """Test server-side verification of valid Razorpay payment signature."""
    with patch("app.services.razorpay_service.settings.RAZORPAY_KEY_ID", "rzp_test_mock_key"), \
         patch("app.services.razorpay_service.settings.RAZORPAY_KEY_SECRET", "mock_secret_key"), \
         patch("razorpay.Client") as MockClient:

        mock_instance = MockClient.return_value
        mock_instance.utility.verify_payment_signature.return_value = True

        response = client.post(
            "/api/v1/razorpay/verify",
            json={
                "razorpay_order_id": "order_mock123",
                "razorpay_payment_id": "pay_mock456",
                "razorpay_signature": "valid_signature_hash"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["verified"] is True
        assert data["razorpay_order_id"] == "order_mock123"
        assert data["razorpay_payment_id"] == "pay_mock456"

def test_razorpay_verify_signature_rejection():
    """Test server-side rejection of invalid Razorpay payment signature."""
    with patch("app.services.razorpay_service.settings.RAZORPAY_KEY_ID", "rzp_test_mock_key"), \
         patch("app.services.razorpay_service.settings.RAZORPAY_KEY_SECRET", "mock_secret_key"), \
         patch("razorpay.Client") as MockClient:

        mock_instance = MockClient.return_value
        mock_instance.utility.verify_payment_signature.side_effect = Exception("Signature mismatch")

        response = client.post(
            "/api/v1/razorpay/verify",
            json={
                "razorpay_order_id": "order_mock123",
                "razorpay_payment_id": "pay_mock456",
                "razorpay_signature": "invalid_signature"
            }
        )

        assert response.status_code == 400
        assert "Razorpay signature verification failed" in response.json()["detail"]

def test_razorpay_failure_pipeline_integration():
    """Test full RecoverAI pipeline integration when Razorpay payment fails."""
    response = client.post(
        "/api/v1/razorpay/report-failure",
        json={
            "razorpay_order_id": "order_mock789",
            "razorpay_payment_id": "pay_failed_123",
            "error_code": "BAD_REQUEST_ERROR",
            "error_description": "Network timeout occurred during payment processing",
            "error_reason": "gateway_timeout",
            "amount": 2499.00,
            "payment_method": "razorpay"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "transaction_id" in data
    assert "workflow_id" in data
    assert data["failure_category"] == "temporary_degradation"
    assert data["recommended_strategy"] in ["RETRY", "SMART_RETRY", "NOTIFY_CUSTOMER"]
    assert data["final_strategy"] in ["RETRY", "NO_ACTION", "ESCALATE", "NOTIFY_CUSTOMER"]
    
    # Revenue recovered assertion: Only > 0 if attempt actually succeeded
    if data["attempt_success"] is True:
        assert data["amount_recovered"] == 2499.00
    else:
        assert data["amount_recovered"] == 0.0
