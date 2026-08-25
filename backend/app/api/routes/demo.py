import uuid
from decimal import Decimal
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.session import get_db
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.api.routes.workflows import create_workflow, trigger_decision, record_attempt
from app.schemas.recovery import WorkflowCreate, AttemptCreate

router = APIRouter()

class ScenarioRequest(BaseModel):
    scenario_type: str = Field(..., description="network_timeout, insufficient_funds, hard_decline, high_value")
    auto_execute_attempt: bool = Field(default=True, description="Whether to auto-simulate attempt execution after decision")

class DemoSeedResponse(BaseModel):
    status: str
    message: str
    customers_seeded: int
    transactions_seeded: int

@router.post("/demo/seed", response_model=DemoSeedResponse, status_code=status.HTTP_200_OK, summary="Idempotently Seed Synthetic Demo Telemetry")
def seed_demo_data(db: Session = Depends(get_db)):
    """Idempotently populates synthetic demo customers and failed transactions for demonstration."""
    # Check idempotency marker
    existing_cust_stmt = select(Customer).where(Customer.email.like("demo_%@example.com"))
    existing_customers = db.scalars(existing_cust_stmt).all()

    if existing_customers:
        tx_count = db.scalar(select(Transaction.id).where(Transaction.customer_id.in_([c.id for c in existing_customers])))
        return DemoSeedResponse(
            status="skipped",
            message="Demo data already exists. Idempotent check prevented duplicate seeding.",
            customers_seeded=len(existing_customers),
            transactions_seeded=1 if tx_count else 0
        )

    # Seed 3 synthetic customers
    demo_cust_1 = Customer(
        id=str(uuid.uuid4()),
        name="Demo Enterprise Customer",
        email="demo_enterprise@example.com",
        total_transactions=12,
        successful_transactions=10,
        failed_transactions=2,
        lifetime_value=Decimal("125000.00"),
        risk_score=Decimal("0.10")
    )
    demo_cust_2 = Customer(
        id=str(uuid.uuid4()),
        name="Demo Pro Customer",
        email="demo_pro@example.com",
        total_transactions=5,
        successful_transactions=4,
        failed_transactions=1,
        lifetime_value=Decimal("15000.00"),
        risk_score=Decimal("0.25")
    )
    demo_cust_3 = Customer(
        id=str(uuid.uuid4()),
        name="Demo Starter Customer",
        email="demo_starter@example.com",
        total_transactions=2,
        successful_transactions=1,
        failed_transactions=1,
        lifetime_value=Decimal("2999.00"),
        risk_score=Decimal("0.40")
    )
    db.add_all([demo_cust_1, demo_cust_2, demo_cust_3])
    db.flush()

    # Seed 4 representative failed transactions for scenarios
    txs = [
        Transaction(
            id=str(uuid.uuid4()),
            customer_id=demo_cust_1.id,
            amount=Decimal("4999.00"),
            currency="INR",
            status="failed",
            failure_reason="gateway_timeout",
            payment_method="upi",
            attempt_number=1
        ),
        Transaction(
            id=str(uuid.uuid4()),
            customer_id=demo_cust_2.id,
            amount=Decimal("2499.00"),
            currency="INR",
            status="failed",
            failure_reason="insufficient_funds",
            payment_method="card",
            attempt_number=1
        ),
        Transaction(
            id=str(uuid.uuid4()),
            customer_id=demo_cust_3.id,
            amount=Decimal("1499.00"),
            currency="INR",
            status="failed",
            failure_reason="stolen_card",
            payment_method="card",
            attempt_number=1
        ),
        Transaction(
            id=str(uuid.uuid4()),
            customer_id=demo_cust_1.id,
            amount=Decimal("75000.00"),
            currency="INR",
            status="failed",
            failure_reason="gateway_timeout",
            payment_method="netbanking",
            attempt_number=1
        ),
    ]
    db.add_all(txs)
    db.commit()

    return DemoSeedResponse(
        status="success",
        message="Synthetic demo data successfully seeded.",
        customers_seeded=3,
        transactions_seeded=4
    )

@router.post("/demo/simulate-scenario", summary="Execute End-to-End Demo Scenario via Core Engine")
def simulate_demo_scenario(payload: ScenarioRequest, db: Session = Depends(get_db)):
    """Executes a 1-click end-to-end recovery scenario reusing existing workflow/decision/policy engine routes."""
    # Map scenario to synthetic transaction parameters
    scenario_configs: Dict[str, Dict[str, Any]] = {
        "network_timeout": {
            "amount": Decimal("3999.00"),
            "reason": "gateway_timeout",
            "method": "upi"
        },
        "insufficient_funds": {
            "amount": Decimal("1999.00"),
            "reason": "insufficient_funds",
            "method": "card"
        },
        "hard_decline": {
            "amount": Decimal("1299.00"),
            "reason": "stolen_card",
            "method": "card"
        },
        "high_value": {
            "amount": Decimal("65000.00"),
            "reason": "network_timeout",
            "method": "netbanking"
        }
    }

    if payload.scenario_type not in scenario_configs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown scenario type '{payload.scenario_type}'. Valid types: {list(scenario_configs.keys())}"
        )

    cfg = scenario_configs[payload.scenario_type]

    # Ensure synthetic demo customer exists
    cust = db.scalar(select(Customer).where(Customer.email == "demo_runner@example.com"))
    if not cust:
        cust = Customer(
            id=str(uuid.uuid4()),
            name="Demo Runner Customer",
            email="demo_runner@example.com",
            total_transactions=1,
            successful_transactions=0,
            failed_transactions=1,
            lifetime_value=Decimal("0.00"),
            risk_score=Decimal("0.10")
        )
        db.add(cust)
        db.flush()

    # 1. Create Transaction
    tx = Transaction(
        id=str(uuid.uuid4()),
        customer_id=cust.id,
        amount=cfg["amount"],
        currency="INR",
        status="failed",
        failure_reason=cfg["reason"],
        payment_method=cfg["method"],
        attempt_number=1
    )
    db.add(tx)
    db.commit()

    # 2. Initiate Workflow (reuses existing endpoint logic)
    wf_res = create_workflow(WorkflowCreate(transaction_id=tx.id), db=db)
    wf_id = wf_res.id

    # 3. Trigger Decision Engine & Policy Check (reuses existing endpoint logic)
    dec_res = trigger_decision(wf_id, db=db)

    # 4. Optionally auto-execute attempt if strategy is retryable
    attempt_res = None
    if payload.auto_execute_attempt and dec_res.final_strategy == "RETRY":
        attempt_res = record_attempt(
            wf_id,
            AttemptCreate(
                success=True,
                amount_recovered=cfg["amount"],
                response_metadata={"scenario": payload.scenario_type, "simulated_gateway": "razorpay_test_mode"}
            ),
            db=db
        )

    return {
        "scenario_type": payload.scenario_type,
        "transaction_id": tx.id,
        "workflow_id": wf_id,
        "failure_category": wf_res.failure_category,
        "recommended_strategy": dec_res.recommended_strategy,
        "final_strategy": dec_res.final_strategy,
        "policy_result": dec_res.policy_result,
        "ai_confidence": dec_res.confidence_score,
        "ai_reasoning": dec_res.reason,
        "explanation_details": dec_res.explanation_details,
        "attempt_recorded": bool(attempt_res),
        "attempt_success": attempt_res.success if attempt_res else None
    }
