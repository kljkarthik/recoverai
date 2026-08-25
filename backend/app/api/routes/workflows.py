from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from app.database.session import get_db
from app.core.config import settings
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.models.recovery_workflow import RecoveryWorkflow
from app.models.recovery_decision import RecoveryDecision
from app.models.recovery_action import RecoveryAction
from app.models.recovery_attempt import RecoveryAttempt
from app.models.audit_log import AuditLog
from app.engine.classifier import FailureClassifier
from app.engine.factory import get_decision_engine
from app.engine.policy import PolicyEngine
from app.schemas.recovery import (
    WorkflowCreate, WorkflowResponse, DecisionResponse, AttemptCreate, AttemptResponse
)

router = APIRouter()

@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED, summary="Initialize Recovery Workflow")
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)):
    """Creates a new recovery workflow for a failed or abandoned transaction."""
    # 1. Fetch transaction
    tx_stmt = select(Transaction).where(Transaction.id == payload.transaction_id)
    tx = db.scalar(tx_stmt)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{payload.transaction_id}' not found."
        )

    if tx.status not in ["failed", "abandoned"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot initiate recovery workflow for transaction with status '{tx.status}'. Must be 'failed' or 'abandoned'."
        )

    # 2. Check for duplicate active workflow
    existing_wf_stmt = select(RecoveryWorkflow).where(
        RecoveryWorkflow.transaction_id == payload.transaction_id,
        RecoveryWorkflow.status.in_(["INITIATED", "IN_PROGRESS"])
    )
    existing_wf = db.scalar(existing_wf_stmt)
    if existing_wf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An active recovery workflow '{existing_wf.id}' already exists for transaction '{payload.transaction_id}'."
        )

    # 3. Classify failure category
    category = FailureClassifier.classify(tx.failure_reason)
    max_retries = payload.max_retries or settings.MAX_RETRY_ATTEMPTS

    # 4. Create workflow
    workflow = RecoveryWorkflow(
        transaction_id=tx.id,
        status="INITIATED",
        failure_category=category,
        current_step=0,
        max_retries=max_retries
    )
    db.add(workflow)
    db.flush()

    # 5. Record AuditLog
    audit_init = AuditLog(
        workflow_id=workflow.id,
        transaction_id=tx.id,
        event_type="WORKFLOW_CREATED",
        actor="system",
        decision="WORKFLOW_INITIALIZED",
        action="INITIATE_WORKFLOW",
        reason=f"Recovery workflow created for failure reason '{tx.failure_reason or 'None'}' categorized as '{category}'.",
        status_result="INITIATED",
        metadata_json={"max_retries": max_retries, "amount": str(tx.amount)}
    )
    db.add(audit_init)
    db.commit()

    # Reload with relationships
    stmt = select(RecoveryWorkflow).where(RecoveryWorkflow.id == workflow.id).options(
        selectinload(RecoveryWorkflow.decisions),
        selectinload(RecoveryWorkflow.actions),
        selectinload(RecoveryWorkflow.attempts)
    )
    return db.scalar(stmt)

@router.get("/workflows", response_model=List[WorkflowResponse], summary="List Recovery Workflows")
def list_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    failure_category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve recovery workflows with filtering and pagination."""
    query = select(RecoveryWorkflow).options(
        selectinload(RecoveryWorkflow.decisions),
        selectinload(RecoveryWorkflow.actions),
        selectinload(RecoveryWorkflow.attempts)
    )
    if status:
        query = query.where(RecoveryWorkflow.status == status)
    if failure_category:
        query = query.where(RecoveryWorkflow.failure_category == failure_category)

    query = query.order_by(RecoveryWorkflow.created_at.desc()).offset(skip).limit(limit)
    return db.scalars(query).all()

@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse, summary="Get Workflow Details")
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Fetch complete workflow record including decisions, actions, and attempts."""
    stmt = select(RecoveryWorkflow).where(RecoveryWorkflow.id == workflow_id).options(
        selectinload(RecoveryWorkflow.decisions),
        selectinload(RecoveryWorkflow.actions),
        selectinload(RecoveryWorkflow.attempts)
    )
    workflow = db.scalar(stmt)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery workflow with ID '{workflow_id}' not found."
        )
    return workflow

@router.post("/workflows/{workflow_id}/decide", response_model=DecisionResponse, summary="Trigger Decision Engine & Policy Check")
def trigger_decision(workflow_id: str, db: Session = Depends(get_db)):
    """Evaluates the transaction through the decision engine and applies safety policy guardrails."""
    # 1. Fetch workflow & transaction
    wf_stmt = select(RecoveryWorkflow).where(RecoveryWorkflow.id == workflow_id)
    workflow = db.scalar(wf_stmt)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery workflow with ID '{workflow_id}' not found."
        )

    tx_stmt = select(Transaction).where(Transaction.id == workflow.transaction_id)
    tx = db.scalar(tx_stmt)
    cust = db.scalar(select(Customer).where(Customer.id == tx.customer_id)) if tx else None

    # Audit: FAILURE_CLASSIFIED
    audit_classified = AuditLog(
        workflow_id=workflow.id,
        transaction_id=tx.id,
        event_type="FAILURE_CLASSIFIED",
        actor="system",
        decision=workflow.failure_category,
        action="CLASSIFY_FAILURE",
        reason=f"Failure classified as '{workflow.failure_category}'.",
        status_result=workflow.failure_category
    )
    db.add(audit_classified)


    # 2. Decision Engine Recommendation
    engine = get_decision_engine()
    rec = engine.recommend_strategy(tx, workflow.failure_category, cust)

    actor_name = rec.explanation_details.get("engine_type", "decision_engine") if rec.explanation_details else "decision_engine"

    # Audit: DECISION_MADE
    audit_decision = AuditLog(
        workflow_id=workflow.id,
        transaction_id=tx.id,
        event_type="DECISION_MADE",
        actor=actor_name,
        decision=rec.recommended_strategy,
        action="RECOMMEND_STRATEGY",
        reason=rec.reason,
        status_result="RECOMMENDED",
        metadata_json=rec.explanation_details
    )
    db.add(audit_decision)

    # 3. Policy Engine Guardrail Evaluation
    pol = PolicyEngine.evaluate(rec.recommended_strategy, tx, workflow, workflow.current_step)

    # Audit: POLICY_CHECKED
    audit_policy = AuditLog(
        workflow_id=workflow.id,
        transaction_id=tx.id,
        event_type="POLICY_CHECKED",
        actor="policy_engine",
        decision=pol.policy_result,
        action=pol.final_strategy,
        reason=pol.reason,
        status_result=pol.policy_result
    )
    db.add(audit_policy)

    # 4. Record RecoveryDecision
    decision_rec = RecoveryDecision(
        workflow_id=workflow.id,
        failure_category=workflow.failure_category,
        recommended_strategy=rec.recommended_strategy,
        final_strategy=pol.final_strategy,
        reason=f"{rec.reason} | Policy: {pol.reason}",
        policy_result=pol.policy_result,
        confidence_score=Decimal(str(rec.confidence_score)),
        explanation_details=rec.explanation_details
    )
    db.add(decision_rec)

    # 5. Update Workflow & Action State
    if pol.final_strategy == "ESCALATE":
        workflow.status = "ESCALATED"
    elif pol.final_strategy == "NO_ACTION":
        workflow.status = "ABORTED"
    else:
        workflow.status = "IN_PROGRESS"

    # Create bounded RecoveryAction record
    action_rec = RecoveryAction(
        transaction_id=tx.id,
        workflow_id=workflow.id,
        action_type=pol.final_strategy,
        reason=pol.reason,
        ai_confidence=Decimal(str(rec.confidence_score)),
        policy_result=pol.policy_result,
        status="PENDING"
    )
    db.add(action_rec)
    db.commit()
    db.refresh(decision_rec)
    return decision_rec

@router.post("/workflows/{workflow_id}/attempt", response_model=AttemptResponse, summary="Execute Simulated Attempt & Record Result")
def record_attempt(workflow_id: str, payload: AttemptCreate, db: Session = Depends(get_db)):
    """Records a simulated recovery attempt execution and updates workflow & transaction states."""
    wf_stmt = select(RecoveryWorkflow).where(RecoveryWorkflow.id == workflow_id)
    workflow = db.scalar(wf_stmt)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery workflow with ID '{workflow_id}' not found."
        )

    if workflow.status not in ["INITIATED", "IN_PROGRESS"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record attempt for workflow in status '{workflow.status}'."
        )

    # Fetch latest pending action
    action_stmt = select(RecoveryAction).where(
        RecoveryAction.workflow_id == workflow.id
    ).order_by(RecoveryAction.created_at.desc())
    action = db.scalar(action_stmt)

    if not action:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recovery action found for this workflow. Please trigger a decision first via /decide."
        )

    # Increment workflow step
    workflow.current_step += 1
    attempt_status = "SUCCESS" if payload.success else "FAILED"
    action.status = attempt_status

    # Create RecoveryAttempt record
    attempt = RecoveryAttempt(
        recovery_action_id=action.id,
        workflow_id=workflow.id,
        attempt_number=workflow.current_step,
        status=attempt_status,
        success=payload.success,
        amount_recovered=payload.amount_recovered or Decimal("0.00"),
        response_metadata=payload.response_metadata or {}
    )
    db.add(attempt)

    tx_stmt = select(Transaction).where(Transaction.id == workflow.transaction_id)
    tx = db.scalar(tx_stmt)
    cust = db.scalar(select(Customer).where(Customer.id == tx.customer_id)) if tx else None

    # Audit: RECOVERY_ATTEMPTED
    audit_attempt = AuditLog(
        workflow_id=workflow.id,
        transaction_id=tx.id,
        event_type="RECOVERY_ATTEMPTED",
        actor="system",
        decision=action.action_type,
        action="EXECUTE_SIMULATED_ATTEMPT",
        reason=f"Simulated attempt #{workflow.current_step} executed for strategy '{action.action_type}'.",
        status_result=attempt_status,
        metadata_json={"success": payload.success, "amount_recovered": str(payload.amount_recovered)}
    )
    db.add(audit_attempt)

    if payload.success:
        workflow.status = "RECOVERED"
        if tx:
            tx.status = "success"
        if cust and payload.amount_recovered:
            cust.successful_transactions += 1
            if cust.failed_transactions > 0:
                cust.failed_transactions -= 1
            cust.lifetime_value += (payload.amount_recovered or Decimal("0.00"))

        # Audit: RECOVERY_COMPLETED
        audit_complete = AuditLog(
            workflow_id=workflow.id,
            transaction_id=tx.id,
            event_type="RECOVERY_COMPLETED",
            actor="system",
            decision="RECOVERED",
            action="REVENUE_RECOVERED",
            reason=f"Recovery successful. Recovered ₹{(payload.amount_recovered or Decimal('0.00')):,.2f}.",
            status_result="SUCCESS"
        )
        db.add(audit_complete)
    else:
        if workflow.current_step >= workflow.max_retries:
            workflow.status = "FAILED"
            audit_failed = AuditLog(
                workflow_id=workflow.id,
                transaction_id=tx.id,
                event_type="RECOVERY_FAILED",
                actor="system",
                decision="EXHAUSTED",
                action="TERMINATE_WORKFLOW",
                reason=f"Maximum retry attempt limit ({workflow.max_retries}) reached without recovery.",
                status_result="FAILED"
            )
            db.add(audit_failed)

    db.commit()
    db.refresh(attempt)
    return attempt
