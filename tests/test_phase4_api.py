import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend folder is in python path
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.main import app
from app.core.config import settings
from app.database.session import get_db
from app.database.base import Base

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


# --- 1. Audit Logs Read-Only Endpoint Test ---
def test_get_audit_logs_read_only(client):
    # First trigger demo scenario to create audit logs
    client.post("/api/v1/demo/simulate-scenario", json={"scenario_type": "network_timeout"})

    response = client.get("/api/v1/audit-logs")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    assert "event_type" in logs[0]
    assert "timestamp" in logs[0]


# --- 2. Customers Directory Endpoint Test ---
def test_get_customers_api(client):
    response = client.get("/api/v1/customers")
    assert response.status_code == 200
    customers = response.json()
    assert isinstance(customers, list)


# --- 3. Demo Data Seeding Idempotency Test ---
def test_demo_seed_idempotency(client):
    # First seed call
    res1 = client.post("/api/v1/demo/seed")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] in ["success", "skipped"]

    # Second seed call (Must be idempotent)
    res2 = client.post("/api/v1/demo/seed")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "skipped"
    assert "idempotent" in data2["message"].lower()


# --- 4. Interactive Demo Scenario Runner Test ---
def test_demo_simulate_scenario_api(client):
    # Test network_timeout scenario
    res_retry = client.post("/api/v1/demo/simulate-scenario", json={"scenario_type": "network_timeout"})
    assert res_retry.status_code == 200
    data_retry = res_retry.json()
    assert data_retry["scenario_type"] == "network_timeout"
    assert data_retry["recommended_strategy"] == "RETRY"
    assert data_retry["final_strategy"] == "RETRY"
    assert data_retry["policy_result"] == "ALLOWED"

    # Test hard_decline scenario (Policy block override)
    res_hard = client.post("/api/v1/demo/simulate-scenario", json={"scenario_type": "hard_decline"})
    assert res_hard.status_code == 200
    data_hard = res_hard.json()
    assert data_hard["scenario_type"] == "hard_decline"
    assert data_hard["final_strategy"] == "NO_ACTION"
    assert data_hard["policy_result"] == "BLOCKED"
