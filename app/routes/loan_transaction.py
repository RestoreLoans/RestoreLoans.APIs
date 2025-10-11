from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyResponse

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

@router.get("/by-user/{user_id}", response_model=list[CompanyResponse])
def get_companies_by_user(user_id: int, db: Session = Depends(get_db)):
    companies = db.query(Company).filter(Company.user_id == user_id).all()
    if not companies:
        raise HTTPException(status_code=404, detail="No companies found for this user")
    return companies

@router.post(
    "/",
    response_model=LoanTransactionResponse
)
def create_loan_transaction(
    data: LoanTransactionCreate,
    db: Session = Depends(get_db)
):
    transaction = LoanTransaction(**data.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get(
    "/",
    response_model=list[LoanTransactionResponse]
)
def read_loan_transactions(
    db: Session = Depends(get_db)
):
    transactions = db.query(LoanTransaction).all()
    return transactions


@router.get(
    "/{transaction_id}",
    response_model=LoanTransactionResponse
)
def read_loan_transaction(
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


@router.put(
    "/{transaction_id}/status",
    response_model=LoanTransactionResponse
)
def update_loan_transaction_status(
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


@router.delete(
    "/{transaction_id}",
    response_model=dict
)
def delete_loan_transaction(
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
    db.delete(transaction)
    db.commit()
    return {"detail": "Transaction deleted"}