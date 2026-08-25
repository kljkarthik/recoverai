from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.schemas.recovery import AuditLogResponse

router = APIRouter()

@router.get("/audit-logs", response_model=List[AuditLogResponse], summary="List Audit Logs (Read-Only)")
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    workflow_id: Optional[str] = None,
    event_type: Optional[str] = None,
    actor: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve immutable audit trail entries with filtering and pagination. Strictly read-only."""
    query = select(AuditLog)
    if workflow_id:
        query = query.where(AuditLog.workflow_id == workflow_id)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if actor:
        query = query.where(AuditLog.actor == actor)

    query = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
    return db.scalars(query).all()
