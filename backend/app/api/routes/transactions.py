from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.session import get_db
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.schemas.transaction import TransactionCreate, TransactionResponse

router = APIRouter()

@router.get("/transactions", response_model=List[TransactionResponse], summary="List Transactions")
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve a list of transactions with optional filtering and pagination."""
    query = select(Transaction)
    if status:
        query = query.where(Transaction.status == status)
    if customer_id:
        query = query.where(Transaction.customer_id == customer_id)
    
    query = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
    result = db.scalars(query).all()
    return result

@router.get("/transactions/{transaction_id}", response_model=TransactionResponse, summary="Get Transaction by ID")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Fetch a specific transaction record by its unique ID."""
    stmt = select(Transaction).where(Transaction.id == transaction_id)
    transaction = db.scalar(stmt)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{transaction_id}' not found."
        )
    return transaction

@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, summary="Create Transaction")
def create_transaction(payload: TransactionCreate, db: Session = Depends(get_db)):
    """Create a new transaction record for an existing customer."""
    # Verify customer exists
    customer_stmt = select(Customer).where(Customer.id == payload.customer_id)
    customer = db.scalar(customer_stmt)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{payload.customer_id}' does not exist."
        )

    # Create transaction
    new_transaction = Transaction(
        customer_id=payload.customer_id,
        amount=payload.amount,
        currency=payload.currency,
        status=payload.status,
        failure_reason=payload.failure_reason,
        payment_method=payload.payment_method,
        attempt_number=payload.attempt_number
    )

    # Update customer statistics
    customer.total_transactions += 1
    if payload.status == "success":
        customer.successful_transactions += 1
        customer.lifetime_value += payload.amount
    elif payload.status == "failed":
        customer.failed_transactions += 1

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction
