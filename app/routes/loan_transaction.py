from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
# Removed unused and unresolved import

from app.schemas.loan_transaction import (
    LoanTransactionCreate,
    LoanTransactionResponse,
    LoanTransactionUpdateStatus,
)
from app.models.loan_transaction import LoanTransaction
from datetime import datetime, timezone

router = APIRouter(
    prefix="/loan-transactions",
    tags=["Loan Transactions"]
)
@router.post(
    "/",
    response_model=LoanTransactionResponse
)
def create_loan_transaction(
    data: LoanTransactionCreate,
    db: Session = Depends(get_db)
):
    transaction = LoanTransaction(**data.dict())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

@router.put(
    "/{transaction_id}/status",
    response_model=LoanTransactionResponse
)
def update_status(
    transaction_id: int,
    status: LoanTransactionUpdateStatus,
    db: Session = Depends(get_db)
):
    transaction = db.query(LoanTransaction).filter(
        LoanTransaction.id == transaction_id
    ).first()
    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )
    transaction.status_approval = status.status_approval
    if status.status_approval == "Approved":
        transaction.date_approved = datetime.now(timezone.utc)
        # TODO: Send actions to bank/account here
    db.commit()
    db.refresh(transaction)
    return transaction

@router.get(
    "/{transaction_id}",
    response_model=LoanTransactionResponse
)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    transaction = db.query(LoanTransaction).filter(
        LoanTransaction.id == transaction_id
    ).first()
    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )
    return transaction