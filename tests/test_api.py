import os
import sys
import uuid
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
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

# PostgreSQL Test Engine (Isolated test DB)
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL_TEST",
    settings.DATABASE_URL_TEST
)

engine_test = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in the isolated test database before running tests, and teardown after."""
    try:
        # Create schema in test database
        Base.metadata.create_all(bind=engine_test)
    except Exception as e:
        pytest.skip(f"Skipping PostgreSQL test database execution (Connection failed: {e})")

    yield

    # Clean up test database
    try:
        Base.metadata.drop_all(bind=engine_test)
    except Exception:
        pass

@pytest.fixture
def db_session():
    """Provides a transactional session for each test, rolling back changes after test completion."""
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency to point to the test database session."""
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
    """Creates a sample customer record in the test database for transaction tests."""
    cust = Customer(
        id=str(uuid.uuid4()),
        name="Test Customer",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        total_transactions=0,
        successful_transactions=0,
        failed_transactions=0,
        lifetime_value=Decimal("0.00"),
        risk_score=Decimal("0.10")
    )
    db_session.add(cust)
    db_session.commit()
    db_session.refresh(cust)
    return cust


# --- 1. Health Endpoint Test ---
def test_health_check_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "timestamp" in data


# --- 2. Create Transaction Test ---
def test_create_transaction_success(client, sample_customer):
    payload = {
        "customer_id": sample_customer.id,
        "amount": 2999.50,
        "currency": "INR",
        "status": "failed",
        "failure_reason": "insufficient_funds",
        "payment_method": "card",
        "attempt_number": 1
    }
    response = client.post("/api/v1/transactions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == sample_customer.id
    assert Decimal(str(data["amount"])) == Decimal("2999.50")
    assert data["status"] == "failed"
    assert data["failure_reason"] == "insufficient_funds"
    assert "id" in data
    assert "created_at" in data


# --- 3. Retrieve Transaction by ID Test ---
def test_get_transaction_by_id(client, sample_customer):
    # First create a transaction
    payload = {
        "customer_id": sample_customer.id,
        "amount": 1500.00,
        "currency": "INR",
        "status": "success",
        "failure_reason": None,
        "payment_method": "upi",
        "attempt_number": 1
    }
    create_res = client.post("/api/v1/transactions", json=payload)
    assert create_res.status_code == 201
    tx_id = create_res.json()["id"]

    # Retrieve by ID
    get_res = client.get(f"/api/v1/transactions/{tx_id}")
    assert get_res.status_code == 200
    tx_data = get_res.json()
    assert tx_data["id"] == tx_id
    assert tx_data["status"] == "success"
    assert tx_data["payment_method"] == "upi"


# --- 4. List Transactions Test ---
def test_list_transactions(client, sample_customer):
    response = client.get("/api/v1/transactions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# --- 5. Basic Validation Failure Test ---
def test_create_transaction_validation_error(client):
    # Amount cannot be <= 0 or missing required fields
    invalid_payload = {
        "customer_id": "non-existent-id",
        "amount": -100.00,  # invalid negative amount
        "status": "failed"
        # missing payment_method
    }
    response = client.post("/api/v1/transactions", json=invalid_payload)
    assert response.status_code == 422  # Unprocessable Entity
    errors = response.json()["detail"]
    assert any(err["loc"] == ["body", "amount"] for err in errors)
    assert any(err["loc"] == ["body", "payment_method"] for err in errors)
