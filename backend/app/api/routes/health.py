from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import get_db
from app.schemas.transaction import HealthCheckResponse

router = APIRouter()

@router.get("/health", response_model=HealthCheckResponse, summary="Health Check Endpoint")
def health_check(db: Session = Depends(get_db)):
    """Verifies that the API service and PostgreSQL database connection are active."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "database": db_status}
        )

    return HealthCheckResponse(
        status="healthy",
        database=db_status,
        timestamp=datetime.now(timezone.utc)
    )
