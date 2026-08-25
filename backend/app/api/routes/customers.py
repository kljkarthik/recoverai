from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.session import get_db
from app.models.customer import Customer
from app.schemas.transaction import CustomerResponse

router = APIRouter()

@router.get("/customers", response_model=List[CustomerResponse], summary="List Customers")
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve synthetic customer directory for demo transaction initialization."""
    query = select(Customer).order_by(Customer.created_at.desc()).offset(skip).limit(limit)
    return db.scalars(query).all()
