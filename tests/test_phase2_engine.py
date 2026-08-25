import os
import sys
import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Ensure backend folder is in python path
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app
from app.core.config import settings
from app.database.session import get_db
from app.database.base import Base
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.recovery_workflow import RecoveryWorkflow
from app.models.audit_log import AuditLog
from app.engine.classifier import FailureClassifier
from app.engine.rule_engine import RuleBasedDecisionEngine
from app.engine.policy import PolicyEngine

TEST_DATABASE_URL = os.getenv("DATABASE_URL_TEST", settings.DATABASE_URL_TEST)
engine_test = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    try:
        Base.metadata.create_all(bind=engine_test)
    except Exception as e:
        pytest.skip(f"PostgreSQL test database connection failed: {e}")

    yield

    try:
        Base.metadata.drop_all(bind=engine_test)
    except Exception:
        pass

@pytest.fixture
def db_session():
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def sample_customer(db_session):
    cust = Customer(
        id=str(uuid.uuid4()),
        name="Phase 2 Customer",
        email=f"phase2_{uuid.uuid4().hex[:8]}@example.com",
        total_transactions=1,
        successful_transactions=0,
        failed_transactions=1,
        lifetime_value=Decimal("0.00"),
        risk_score=Decimal("0.20")
    )
    db_session.add(cust)
    db_session.commit()
    db_session.refresh(cust)
    return cust

@pytest.fixture
def failed_transaction(db_session, sample_customer):
    tx = Transaction(
        id=str(uuid.uuid4()),
        customer_id=sample_customer.id,
        amount=Decimal("4999.00"),
        currency="INR",
        status="failed",
        failure_reason="gateway_timeout",
        payment_method="upi",
        attempt_number=1
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)
    return tx


# --- 1. Failure Classifier Unit Tests ---
def test_failure_classifier():
    assert FailureClassifier.classify("gateway_timeout") == FailureClassifier.TEMPORARY_DEGRADATION
    assert FailureClassifier.classify("insufficient_funds") == FailureClassifier.INSUFFICIENT_FUNDS
    assert FailureClassifier.classify("network_timeout") == FailureClassifier.NETWORK_TIMEOUT
    assert FailureClassifier.classify("card_expired") == FailureClassifier.INVALID_DETAILS
    assert FailureClassifier.classify("stolen_card") == FailureClassifier.HARD_DECLINE
    assert FailureClassifier.classify("unknown_random_error") == FailureClassifier.UNKNOWN_FAILURE


# --- 2. Rule Engine & Policy Engine Unit Tests ---
def test_rule_engine_and_policy(db_session, failed_transaction):
    engine = RuleBasedDecisionEngine()
    
    # Standard temporary degradation -> RETRY
    rec = engine.recommend_strategy(failed_transaction, FailureClassifier.TEMPORARY_DEGRADATION)
    assert rec.recommended_strategy == "RETRY"
    assert rec.confidence_score == 1.0
    assert "rule_triggered" in rec.explanation_details

    # Policy Check
    wf = RecoveryWorkflow(transaction_id=failed_transaction.id, failure_category="temporary_degradation", current_step=0)
    policy_res = PolicyEngine.evaluate(rec.recommended_strategy, failed_transaction, wf, attempt_count=0)
    assert policy_res.allowed is True
    assert policy_res.final_strategy == "RETRY"

    # Policy Guardrail: Hard Decline Block
    wf_hard = RecoveryWorkflow(transaction_id=failed_transaction.id, failure_category="hard_decline", current_step=0)
    policy_hard = PolicyEngine.evaluate("RETRY", failed_transaction, wf_hard, attempt_count=0)
    assert policy_hard.allowed is False
    assert policy_hard.policy_result == "BLOCKED"
    assert policy_hard.final_strategy == "NO_ACTION"

    # Policy Guardrail: High Value Escalation (e.g. ₹60,000)
    tx_high = Transaction(
        id=str(uuid.uuid4()),
        customer_id=failed_transaction.customer_id,
        amount=Decimal("60000.00"),
        currency="INR",
        status="failed",
        failure_reason="gateway_timeout",
        payment_method="card"
    )
    policy_high = PolicyEngine.evaluate("RETRY", tx_high, wf, attempt_count=0)
    assert policy_high.allowed is False
    assert policy_high.policy_result == "ESCALATED"
    assert policy_high.final_strategy == "ESCALATE"


# --- 3. End-to-End Workflow API Lifecycle Test ---
def test_workflow_lifecycle_api(client, failed_transaction, db_session):
    # A. Initialize Workflow
    init_res = client.post("/api/v1/workflows", json={"transaction_id": failed_transaction.id})
    assert init_res.status_code == 201
    wf_data = init_res.json()
    wf_id = wf_data["id"]
    assert wf_data["status"] == "INITIATED"
    assert wf_data["failure_category"] == FailureClassifier.TEMPORARY_DEGRADATION

    # B. Trigger Decision & Policy Check
    decide_res = client.post(f"/api/v1/workflows/{wf_id}/decide")
    assert decide_res.status_code == 200
    dec_data = decide_res.json()
    assert dec_data["recommended_strategy"] == "RETRY"
    assert dec_data["final_strategy"] == "RETRY"
    assert dec_data["policy_result"] == "ALLOWED"
    assert "explanation_details" in dec_data

    # C. Execute Simulated Recovery Attempt (Success)
    attempt_res = client.post(f"/api/v1/workflows/{wf_id}/attempt", json={
        "success": True,
        "amount_recovered": 4999.00,
        "response_metadata": {"gateway": "simulated_razorpay", "status": "captured"}
    })
    assert attempt_res.status_code == 200
    att_data = attempt_res.json()
    assert att_data["success"] is True
    assert att_data["attempt_number"] == 1

    # D. Verify Updated Workflow Status
    get_wf = client.get(f"/api/v1/workflows/{wf_id}")
    assert get_wf.status_code == 200
    assert get_wf.json()["status"] == "RECOVERED"


# --- 4. Recovery Metrics API Test ---
def test_recovery_metrics_api(client):
    response = client.get("/api/v1/metrics/recovery")
    assert response.status_code == 200
    metrics = response.json()
    assert "revenue_at_risk" in metrics
    assert "recovery_attempts" in metrics
    assert "successful_recoveries" in metrics
    assert "recovery_rate" in metrics
    assert "revenue_recovered" in metrics
    assert 0.0 <= metrics["recovery_rate"] <= 100.0



# --- 5. Audit Log Traceability Test ---
def test_audit_log_traceability(db_session, failed_transaction, client):
    # Create workflow and decide
    wf_res = client.post("/api/v1/workflows", json={"transaction_id": failed_transaction.id})
    wf_id = wf_res.json()["id"]
    client.post(f"/api/v1/workflows/{wf_id}/decide")

    # Fetch audit logs
    stmt = select(AuditLog).where(AuditLog.workflow_id == wf_id)
    logs = db_session.scalars(stmt).all()
    event_types = [log.event_type for log in logs]
    
    assert "WORKFLOW_CREATED" in event_types
    assert "FAILURE_CLASSIFIED" in event_types
    assert "DECISION_MADE" in event_types
    assert "POLICY_CHECKED" in event_types
