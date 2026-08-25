from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, Integer
from app.database.session import get_db
from app.models.transaction import Transaction
from app.models.recovery_attempt import RecoveryAttempt
from app.schemas.recovery import RecoveryMetricsResponse

router = APIRouter()

@router.get("/metrics/recovery", response_model=RecoveryMetricsResponse, summary="Get Revenue Recovery Metrics")
def get_recovery_metrics(db: Session = Depends(get_db)):
    """Computes aggregate real-time revenue recovery metrics across all transactions and workflows."""
    
    # 1. Total failed/abandoned transactions & revenue at risk
    tx_stmt = select(
        func.count(Transaction.id).label("total_failed"),
        func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label("at_risk")
    ).where(Transaction.status.in_(["failed", "abandoned"]))
    tx_res = db.execute(tx_stmt).one()
    total_failed = tx_res.total_failed or 0
    at_risk = Decimal(str(tx_res.at_risk or 0))

    # 2. Total recovery attempts
    attempts_count_stmt = select(func.count(RecoveryAttempt.id))
    total_attempts = db.scalar(attempts_count_stmt) or 0

    # 3. Successful recoveries count
    success_stmt = select(func.count(RecoveryAttempt.id)).where(RecoveryAttempt.success == True)
    successful_count = db.scalar(success_stmt) or 0

    # 4. Revenue recovered
    recovered_stmt = select(
        func.coalesce(func.sum(RecoveryAttempt.amount_recovered), Decimal("0.00"))
    ).where(RecoveryAttempt.success == True)
    revenue_recovered = Decimal(str(db.scalar(recovered_stmt) or 0))

    # 5. Recovery rate percentage
    recovery_rate = float((successful_count / total_failed * 100.0)) if total_failed > 0 else 0.0

    return RecoveryMetricsResponse(
        revenue_at_risk=at_risk,
        recovery_attempts=total_attempts,
        successful_recoveries=successful_count,
        recovery_rate=round(recovery_rate, 2),
        revenue_recovered=revenue_recovered,
        total_failed_transactions=total_failed
    )
