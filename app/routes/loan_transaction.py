from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyResponse
from app.schemas.email import SendLoanEmailRequest
from app.services.email_service import email_service  # Change from 'email' to 'email_service'


from app.schemas.loan_transaction import (
    LoanTransactionCreate,
    LoanTransactionResponse,
    LoanTransactionUpdateStatus,
)
from app.models.loan_transaction import LoanTransaction
from datetime import datetime, timezone
from typing import Optional
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse


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

@router.patch(
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


@router.post("/send-loan-email", response_model=dict)
def send_loan_email(
    email_data: SendLoanEmailRequest,
    db: Session = Depends(get_db)
):
    # Get the transaction
    transaction = db.query(LoanTransaction).filter(
        LoanTransaction.id == email_data.transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )
    
    try:
        if email_data.email_type == "application":
            email_service.send_loan_application_email(
                borrower_name=transaction.borrower,
                loan_id=transaction.loan_id,
                amount=transaction.loan_amount,
                to_emails=email_data.recipient_emails
            )
        
        elif email_data.email_type == "approval":
            email_service.send_loan_approval_email(
                borrower_name=transaction.borrower,
                loan_id=transaction.loan_id,
                amount=transaction.loan_amount,
                account_no=transaction.account_no or "N/A",
                to_emails=email_data.recipient_emails
            )
        
        elif email_data.email_type == "rejection":
            email_service.send_loan_rejection_email(
                borrower_name=transaction.borrower,
                loan_id=transaction.loan_id,
                reason=email_data.rejection_reason or "Not specified",
                to_emails=email_data.recipient_emails
            )
        
        elif email_data.email_type == "custom":
            email_service.send_custom_loan_email(
                borrower_name=transaction.borrower,
                loan_id=transaction.loan_id,
                amount=transaction.loan_amount,
                status=transaction.status_approval,
                message=(
                    email_data.custom_message
                    or "Your loan status has been updated."
                ),
                to_emails=email_data.recipient_emails
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid email type. Use: application, approval, "
                    "rejection, or custom"
                )
            )
        
        return {
            "success": True,
            "message": (
                f"Email sent successfully to "
                f"{len(email_data.recipient_emails)} recipient(s)"
            ),
            "email_type": email_data.email_type
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )

@router.post("/mapping-insert", response_model=TransactionResponse)
def mapping_insert_transaction(
    transaction_id: int,
    account_no: str,
    db: Session = Depends(get_db)
):
    """
    Create a transaction record from a loan transaction.
    Maps loan_transaction data to transactions table.
    """
    # Get the loan transaction
    loan_transaction = db.query(LoanTransaction).filter(
        LoanTransaction.id == transaction_id
    ).first()
    
    if not loan_transaction:
        raise HTTPException(
            status_code=404,
            detail="Loan transaction not found"
        )
    
    # Check if transaction already exists for this loan
    existing_transaction = db.query(Transaction).filter(
        Transaction.loan_id == loan_transaction.loan_id
    ).first()
    
    if existing_transaction:
        raise HTTPException(
            status_code=400,
            detail="Transaction already exists for this loan"
        )
    
    # Create new transaction record
    new_transaction = Transaction(
        loan_id=loan_transaction.loan_id,
        user_id=loan_transaction.user_id,
        loan_amount=loan_transaction.loan_amount,
        account_no=account_no,
        status_approval=loan_transaction.status_approval,
        date_approved=loan_transaction.date_approved
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return new_transaction


@router.post("/mapping-insert-bulk", response_model=dict)
def mapping_insert_bulk_transactions(
    transaction_ids: list[int],
    account_no: str,
    db: Session = Depends(get_db)
):
    """
    Create multiple transaction records from loan transactions.
    Bulk mapping operation.
    """
    created_count = 0
    skipped_count = 0
    created_ids = []
    
    for transaction_id in transaction_ids:
        # Get loan transaction
        loan_transaction = db.query(LoanTransaction).filter(
            LoanTransaction.id == transaction_id
        ).first()
        
        if not loan_transaction:
            skipped_count += 1
            continue
        
        # Check if already exists
        existing = db.query(Transaction).filter(
            Transaction.loan_id == loan_transaction.loan_id
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # Create transaction
        new_transaction = Transaction(
            loan_id=loan_transaction.loan_id,
            user_id=loan_transaction.user_id,
            loan_amount=loan_transaction.loan_amount,
            account_no=account_no,
            status_approval=loan_transaction.status_approval,
            date_approved=loan_transaction.date_approved
        )
        
        db.add(new_transaction)
        db.flush()
        created_ids.append(new_transaction.id)
        created_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "created_count": created_count,
        "skipped_count": skipped_count,
        "created_transaction_ids": created_ids
    }