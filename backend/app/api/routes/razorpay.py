import uuid
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.session import get_db
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.audit_log import AuditLog
from app.schemas.razorpay import (
    RazorpayOrderCreate, RazorpayOrderResponse,
    RazorpayVerifyRequest, RazorpayVerifyResponse,
    RazorpayFailureRequest, RazorpayFailureResponse
)
from app.services.razorpay_service import (
    razorpay_service, RazorpayConfigError, RazorpayVerificationError
)
from app.api.routes.workflows import create_workflow, trigger_decision, record_attempt
from app.schemas.recovery import WorkflowCreate, AttemptCreate

router = APIRouter()

@router.post(
    "/razorpay/orders",
    response_model=RazorpayOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Razorpay Test Mode Order"
)
def create_razorpay_order(payload: RazorpayOrderCreate):
    """Creates a Razorpay Test Mode order converting INR to paise.
    Returns safe order details including public key_id. Never exposes secret.
    """
    try:
        res = razorpay_service.create_order(
            amount_inr=payload.amount,
            currency=payload.currency,
            receipt=payload.receipt
        )
        return RazorpayOrderResponse(**res)
    except RazorpayConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Razorpay order: {str(e)}"
        )

@router.post(
    "/razorpay/verify",
    response_model=RazorpayVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Razorpay Payment Signature Server-Side"
)
def verify_razorpay_payment(payload: RazorpayVerifyRequest, db: Session = Depends(get_db)):
    """Verifies Razorpay HMAC SHA256 signature server-side.
    Never trusts frontend-only payment success.
    """
    try:
        is_valid = razorpay_service.verify_payment_signature(
            razorpay_order_id=payload.razorpay_order_id,
            razorpay_payment_id=payload.razorpay_payment_id,
            razorpay_signature=payload.razorpay_signature
        )

        if not is_valid:
            raise RazorpayVerificationError("Signature verification failed.")

        # Ensure demo/real customer exists
        cust = db.scalar(select(Customer).where(Customer.email == "razorpay_user@example.com"))
        if not cust:
            cust = Customer(
                id=str(uuid.uuid4()),
                name="Razorpay Test Customer",
                email="razorpay_user@example.com",
                total_transactions=1,
                successful_transactions=1,
                failed_transactions=0,
                lifetime_value=Decimal("0.00"),
                risk_score=Decimal("0.10")
            )
            db.add(cust)
            db.flush()

        # Record successful verified transaction
        tx = Transaction(
            id=str(uuid.uuid4()),
            customer_id=cust.id,
            amount=Decimal("1499.00"),  # default or dynamic
            currency="INR",
            status="success",
            payment_method="razorpay",
            attempt_number=1
        )
        db.add(tx)

        # Audit log for verified Razorpay payment
        audit = AuditLog(
            transaction_id=tx.id,
            event_type="PAYMENT_VERIFIED",
            actor="razorpay_sdk",
            decision="VERIFIED",
            action="RECORD_SUCCESSFUL_PAYMENT",
            reason=f"Payment signature verified server-side for Order '{payload.razorpay_order_id}' and Payment '{payload.razorpay_payment_id}'.",
            status_result="SUCCESS",
            metadata_json={
                "razorpay_order_id": payload.razorpay_order_id,
                "razorpay_payment_id": payload.razorpay_payment_id
            }
        )
        db.add(audit)
        db.commit()

        return RazorpayVerifyResponse(
            status="success",
            verified=True,
            razorpay_order_id=payload.razorpay_order_id,
            razorpay_payment_id=payload.razorpay_payment_id,
            message="Razorpay payment signature verified successfully server-side."
        )

    except RazorpayConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except RazorpayVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification process failed: {str(e)}"
        )

@router.post(
    "/razorpay/report-failure",
    response_model=RazorpayFailureResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Razorpay Payment Failure via RecoverAI Pipeline"
)
def report_razorpay_failure(payload: RazorpayFailureRequest, db: Session = Depends(get_db)):
    """Receives Razorpay payment failure event and runs it through RecoverAI's 7-step autonomous recovery engine."""
    # Ensure customer exists
    cust = db.scalar(select(Customer).where(Customer.email == "razorpay_user@example.com"))
    if not cust:
        cust = Customer(
            id=str(uuid.uuid4()),
            name="Razorpay Test Customer",
            email="razorpay_user@example.com",
            total_transactions=1,
            successful_transactions=0,
            failed_transactions=1,
            lifetime_value=Decimal("0.00"),
            risk_score=Decimal("0.15")
        )
        db.add(cust)
        db.flush()

    amount_dec = Decimal(str(payload.amount))

    # 1. Create Transaction in RecoverAI DB
    tx = Transaction(
        id=str(uuid.uuid4()),
        customer_id=cust.id,
        amount=amount_dec,
        currency="INR",
        status="failed",
        failure_reason=payload.error_reason or "gateway_timeout",
        payment_method=payload.payment_method or "razorpay",
        attempt_number=1
    )

    db.add(tx)
    db.commit()

    # 2. Initiate Workflow
    wf_res = create_workflow(WorkflowCreate(transaction_id=tx.id), db=db)
    wf_id = wf_res.id

    # 3. Trigger Decision Engine & Policy Check
    dec_res = trigger_decision(wf_id, db=db)

    # 4. Attempt execution (ONLY mark revenue recovered if attempt actually succeeds)
    attempt_recorded = False
    attempt_success = None
    recovered_amount_val = 0.0

    if dec_res.final_strategy == "RETRY":
        # Simulate recovery attempt for retryable failures
        attempt_res = record_attempt(
            wf_id,
            AttemptCreate(
                success=True,  # Test mode simulated retry recovery success
                amount_recovered=amount_dec,
                response_metadata={
                    "gateway": "razorpay_test_mode",
                    "razorpay_order_id": payload.razorpay_order_id,
                    "error_reason": payload.error_reason
                }
            ),
            db=db
        )
        attempt_recorded = True
        attempt_success = attempt_res.success
        if attempt_res.success:
            recovered_amount_val = float(amount_dec)
    elif dec_res.final_strategy in ["NO_ACTION", "ESCALATE", "NOTIFY_CUSTOMER"]:
        # Blocked, escalated, or outreach actions: revenue is NOT marked recovered
        attempt_recorded = False
        attempt_success = False
        recovered_amount_val = 0.0

    return RazorpayFailureResponse(
        status="completed",
        transaction_id=tx.id,
        workflow_id=wf_id,
        failure_category=wf_res.failure_category,
        recommended_strategy=dec_res.recommended_strategy,
        final_strategy=dec_res.final_strategy,
        policy_result=dec_res.policy_result,
        ai_confidence=float(dec_res.confidence_score),
        ai_reasoning=dec_res.reason,
        attempt_recorded=attempt_recorded,
        attempt_success=attempt_success,
        amount_recovered=recovered_amount_val
    )
