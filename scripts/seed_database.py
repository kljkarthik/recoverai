import os
import sys
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta

# Ensure backend folder is in python path
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine
from app.database.base import Base
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.audit_log import AuditLog

def seed_database():
    """Seeds exactly 3 synthetic customers and 10 synthetic transactions for Phase 1 verification."""
    print("Starting database seeding (Phase 1)...")
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # Check if database already has data
        existing_customers = db.query(Customer).count()
        if existing_customers > 0:
            print(f"Database already contains {existing_customers} customer(s). Skipping seed.")
            return

        # 1. Create 3 synthetic customers
        c1 = Customer(
            id=str(uuid.uuid4()),
            name="Aarav Sharma",
            email="aarav.sharma@example.com",
            total_transactions=4,
            successful_transactions=3,
            failed_transactions=1,
            lifetime_value=Decimal("14999.00"),
            risk_score=Decimal("0.15")
        )
        c2 = Customer(
            id=str(uuid.uuid4()),
            name="Priya Patel",
            email="priya.patel@example.com",
            total_transactions=3,
            successful_transactions=1,
            failed_transactions=2,
            lifetime_value=Decimal("2499.00"),
            risk_score=Decimal("0.45")
        )
        c3 = Customer(
            id=str(uuid.uuid4()),
            name="Rohan Verma",
            email="rohan.verma@example.com",
            total_transactions=3,
            successful_transactions=1,
            failed_transactions=2,
            lifetime_value=Decimal("4999.00"),
            risk_score=Decimal("0.30")
        )

        db.add_all([c1, c2, c3])
        db.commit()

        print(f"Seeded 3 customers: {c1.name}, {c2.name}, {c3.name}")

        now = datetime.now(timezone.utc)

        # 2. Create 10 synthetic transactions
        transactions_data = [
            # Customer 1 transactions
            {"customer": c1, "amount": Decimal("4999.00"), "currency": "INR", "status": "success", "failure_reason": None, "payment_method": "upi", "attempt_number": 1, "delta_days": 10},
            {"customer": c1, "amount": Decimal("4999.00"), "currency": "INR", "status": "success", "failure_reason": None, "payment_method": "upi", "attempt_number": 1, "delta_days": 7},
            {"customer": c1, "amount": Decimal("5001.00"), "currency": "INR", "status": "success", "failure_reason": None, "payment_method": "card", "attempt_number": 1, "delta_days": 3},
            {"customer": c1, "amount": Decimal("4999.00"), "currency": "INR", "status": "failed", "failure_reason": "insufficient_funds", "payment_method": "card", "attempt_number": 1, "delta_hours": 2},

            # Customer 2 transactions
            {"customer": c2, "amount": Decimal("2499.00"), "currency": "INR", "status": "success", "failure_reason": None, "payment_method": "netbanking", "attempt_number": 1, "delta_days": 15},
            {"customer": c2, "amount": Decimal("2499.00"), "currency": "INR", "status": "failed", "failure_reason": "card_expired", "payment_method": "card", "attempt_number": 1, "delta_days": 5},
            {"customer": c2, "amount": Decimal("2499.00"), "currency": "INR", "status": "failed", "failure_reason": "payment_gateway_timeout", "payment_method": "upi", "attempt_number": 1, "delta_hours": 5},

            # Customer 3 transactions
            {"customer": c3, "amount": Decimal("4999.00"), "currency": "INR", "status": "success", "failure_reason": None, "payment_method": "card", "attempt_number": 1, "delta_days": 12},
            {"customer": c3, "amount": Decimal("4999.00"), "currency": "INR", "status": "abandoned", "failure_reason": "checkout_abandonment", "payment_method": "upi", "attempt_number": 1, "delta_days": 2},
            {"customer": c3, "amount": Decimal("4999.00"), "currency": "INR", "status": "failed", "failure_reason": "soft_decline_temporary_bank_error", "payment_method": "card", "attempt_number": 2, "delta_hours": 1},
        ]

        seeded_transactions = []
        for t_data in transactions_data:
            c = t_data["customer"]
            dt = now
            if "delta_days" in t_data:
                dt = now - timedelta(days=t_data["delta_days"])
            elif "delta_hours" in t_data:
                dt = now - timedelta(hours=t_data["delta_hours"])

            tx = Transaction(
                id=str(uuid.uuid4()),
                customer_id=c.id,
                amount=t_data["amount"],
                currency=t_data["currency"],
                status=t_data["status"],
                failure_reason=t_data["failure_reason"],
                payment_method=t_data["payment_method"],
                attempt_number=t_data["attempt_number"],
                created_at=dt
            )
            seeded_transactions.append(tx)

            # Audit log entry for failure events
            if t_data["status"] in ["failed", "abandoned"]:
                audit = AuditLog(
                    id=str(uuid.uuid4()),
                    transaction_id=tx.id,
                    event_type="payment_failure_detected",
                    actor="system",
                    decision="LOGGED_FOR_RECOVERY",
                    reason=f"Failure reason: {t_data['failure_reason'] or 'unknown'}",
                    metadata_json={"amount": str(t_data["amount"]), "payment_method": t_data["payment_method"]},
                    timestamp=dt
                )
                db.add(audit)

        db.add_all(seeded_transactions)
        db.commit()

        print(f"Seeded {len(seeded_transactions)} transactions successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
