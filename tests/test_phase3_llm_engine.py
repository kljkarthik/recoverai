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
from app.engine.llm_engine import LLMDecisionEngine
from app.engine.rule_engine import RuleBasedDecisionEngine
from app.engine.policy import PolicyEngine
from app.engine.providers import MockLLMProvider, LLMRecommendationSchema

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
        name="John Doe PII Private",
        email="john.private.pii@example.com",
        total_transactions=5,
        successful_transactions=4,
        failed_transactions=1,
        lifetime_value=Decimal("15000.00"),
        risk_score=Decimal("0.15")
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
        amount=Decimal("2999.00"),
        currency="INR",
        status="failed",
        failure_reason="insufficient_funds",
        payment_method="upi",
        attempt_number=1
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)
    return tx


# --- 1. LLM Decision Engine Valid Recommendation Test ---
def test_llm_engine_valid_recommendation(failed_transaction, sample_customer):
    provider = MockLLMProvider(mode=MockLLMProvider.VALID)
    engine = LLMDecisionEngine(provider=provider)

    rec = engine.recommend_strategy(failed_transaction, FailureClassifier.INSUFFICIENT_FUNDS, sample_customer)
    assert rec.recommended_strategy == "NOTIFY_CUSTOMER"
    assert rec.confidence_score >= 0.90
    assert rec.explanation_details["engine_type"] == "llm"
    assert rec.explanation_details["fallback_used"] is False
    assert "primary_risk_factor" in rec.explanation_details


# --- 2. Deterministic Fallback Scenarios ---
def test_llm_engine_fallback_on_timeout(failed_transaction, sample_customer):
    provider = MockLLMProvider(mode=MockLLMProvider.TIMEOUT)
    engine = LLMDecisionEngine(provider=provider)

    rec = engine.recommend_strategy(failed_transaction, FailureClassifier.INSUFFICIENT_FUNDS, sample_customer)
    assert rec.recommended_strategy == "NOTIFY_CUSTOMER"  # Rule engine fallback strategy
    assert rec.explanation_details["engine_type"] == "llm_fallback"
    assert rec.explanation_details["fallback_used"] is True
    assert "timed out" in rec.explanation_details["fallback_reason"].lower()

def test_llm_engine_fallback_on_provider_error(failed_transaction, sample_customer):
    provider = MockLLMProvider(mode=MockLLMProvider.PROVIDER_ERROR)
    engine = LLMDecisionEngine(provider=provider)

    rec = engine.recommend_strategy(failed_transaction, FailureClassifier.INSUFFICIENT_FUNDS, sample_customer)
    assert rec.recommended_strategy == "NOTIFY_CUSTOMER"
    assert rec.explanation_details["engine_type"] == "llm_fallback"
    assert rec.explanation_details["fallback_used"] is True
    assert "failed" in rec.explanation_details["fallback_reason"].lower()

def test_llm_engine_fallback_on_malformed_response(failed_transaction, sample_customer):
    provider = MockLLMProvider(mode=MockLLMProvider.MALFORMED)
    engine = LLMDecisionEngine(provider=provider)

    rec = engine.recommend_strategy(failed_transaction, FailureClassifier.INSUFFICIENT_FUNDS, sample_customer)
    assert rec.explanation_details["engine_type"] == "llm_fallback"
    assert rec.explanation_details["fallback_used"] is True

def test_llm_engine_fallback_on_invalid_strategy(failed_transaction, sample_customer):
    provider = MockLLMProvider(mode=MockLLMProvider.INVALID_STRATEGY)
    engine = LLMDecisionEngine(provider=provider)

    rec = engine.recommend_strategy(failed_transaction, FailureClassifier.INSUFFICIENT_FUNDS, sample_customer)
    assert rec.explanation_details["engine_type"] == "llm_fallback"
    assert rec.explanation_details["fallback_used"] is True

def test_llm_engine_fallback_on_low_confidence(failed_transaction, sample_customer):
    provider = MockLLMProvider(mode=MockLLMProvider.LOW_CONFIDENCE)
    engine = LLMDecisionEngine(provider=provider)

    rec = engine.recommend_strategy(failed_transaction, FailureClassifier.INSUFFICIENT_FUNDS, sample_customer)
    assert rec.explanation_details["engine_type"] == "llm_fallback"
    assert rec.explanation_details["fallback_used"] is True
    assert "below minimum threshold" in rec.explanation_details["fallback_reason"]


# --- 3. Interaction with Policy Engine (Safety Override) ---
def test_llm_recommendation_overridden_by_policy(failed_transaction, sample_customer):
    # LLM recommends RETRY, but failure category is HARD_DECLINE
    provider = MockLLMProvider(mode=MockLLMProvider.VALID)
    engine = LLMDecisionEngine(provider=provider)

    # Force hard decline transaction
    tx_hard = Transaction(
        id=str(uuid.uuid4()),
        customer_id=sample_customer.id,
        amount=Decimal("1200.00"),
        currency="INR",
        status="failed",
        failure_reason="card_stolen",
        payment_method="card"
    )

    rec = engine.recommend_strategy(tx_hard, FailureClassifier.HARD_DECLINE, sample_customer)
    wf = RecoveryWorkflow(transaction_id=tx_hard.id, failure_category="hard_decline", current_step=0)

    policy_res = PolicyEngine.evaluate(rec.recommended_strategy, tx_hard, wf, attempt_count=0)
    assert policy_res.allowed is False
    assert policy_res.policy_result == "BLOCKED"
    assert policy_res.final_strategy == "NO_ACTION"


# --- 4. Zero PII Context Privacy Verification ---
def test_prompt_privacy_no_pii(failed_transaction, sample_customer):
    engine = LLMDecisionEngine(provider=MockLLMProvider())
    prompt = engine._build_anonymized_prompt(failed_transaction, FailureClassifier.INSUFFICIENT_FUNDS, sample_customer)

    # Ensure PII like full name or email address are scrubbed
    assert sample_customer.name not in prompt
    assert sample_customer.email not in prompt
    assert "total_transactions" in prompt
    assert "lifetime_value_inr" in prompt


# --- 5. End-to-End API Test with Default LLM Engine ---
def test_api_workflow_decide_with_llm(client, failed_transaction):
    # 1. Initialize workflow
    init_res = client.post("/api/v1/workflows", json={"transaction_id": failed_transaction.id})
    assert init_res.status_code == 201
    wf_id = init_res.json()["id"]

    # 2. Trigger decision (uses default LLM decision engine with mock provider)
    decide_res = client.post(f"/api/v1/workflows/{wf_id}/decide")
    assert decide_res.status_code == 200
    data = decide_res.json()

    assert data["workflow_id"] == wf_id
    assert "recommended_strategy" in data
    assert "final_strategy" in data
    assert "policy_result" in data
    assert data["explanation_details"]["engine_type"] in ["llm", "llm_fallback"]
