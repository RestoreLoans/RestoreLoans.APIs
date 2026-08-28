import requests as http_requests
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyResponse
from app.schemas.email import SendLoanEmailRequest
from app.services.email_service import email_service  # Change from 'email' to 'email_service'

from pydantic import BaseModel
from typing import List
import logging


from app.schemas.loan_transaction import (
    LoanTransactionCreate,
    LoanTransactionResponse,
    LoanTransactionUpdateStatus,
)
from app.models.loan_transaction import LoanTransaction
from datetime import datetime, timezone
from typing import Optional, List
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse


class MappingInsertRequest(BaseModel):
    transaction_id: int
    account_no: str
    to_emails: Optional[List[str]] = None

class MappingInsertBulkRequest(BaseModel):
    transaction_ids: List[int]
    account_no: str
    to_emails: Optional[List[str]] = None


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
                to_emails=email_data.recipient_emails,
                custom_message=email_data.custom_message,
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

@router.post("/send-application-docs-email")
def send_application_docs_email(
    transaction_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Send the applicant's documents to applicants@restoreloans.co.za.

    Downloads the ID document, bank statement and proof of residence
    attached to the loan record and emails them to the internal
    review inbox with subject 'New Loan Application'.
    """
    from app.models.loan import Loan

    txn = db.query(LoanTransaction).filter(
        LoanTransaction.id == transaction_id
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    loan = db.query(Loan).filter(Loan.id == txn.loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found for transaction")

    attachments = []
    doc_urls = [
        (loan.id_path, "id_document"),
        (loan.bank_path, "bank_statement"),
        (loan.proof_of_residence_path, "proof_of_residence"),
    ]
    for url, label in doc_urls:
        if url:
            try:
                resp = http_requests.get(url, timeout=30)
                resp.raise_for_status()
                filename = url.split("/")[-1].split("?")[0] or f"{label}.pdf"
                attachments.append((resp.content, filename))
            except Exception as exc:
                logging.warning("Could not download %s from %s: %s", label, url, exc)

    loan_type_str = str(loan.loan_type.value) if hasattr(loan.loan_type, "value") else str(loan.loan_type) if loan.loan_type else ""
    user = None
    from app.models.user import User
    user = db.query(User).filter(User.id == txn.user_id).first()
    user_details = None
    if user:
        user_details = {
            "title": user.title,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "id_number": user.id_number,
            "email": user.email,
            "phone_number": user.phone_number,
            "gender": user.gender.value if hasattr(user.gender, "value") else user.gender,
            "homephone": user.homephone,
            "home_add1": user.home_add1,
            "home_add2": user.home_add2,
            "suburb": user.suburb,
            "town": user.town,
            "postal_code": user.postal_code,
            "language": user.language,
            "dob": user.dob.isoformat() if user.dob else None,
            "nationality": user.nationality,
        }
    try:
        email_service.send_application_with_docs_email(
            borrower_name=txn.borrower,
            loan_id=txn.loan_id,
            amount=txn.loan_amount,
            loan_type=loan_type_str,
            interest_rate=loan.interest_rate or 0,
            loan_term=loan.loan_term or 0,
            to_emails=["applicants@restoreloans.co.za"],
            attachments=attachments or None,
            user_details=user_details,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send application docs email: {exc}"
        )

    return {
        "success": True,
        "message": "Application documents sent to applicants@restoreloans.co.za",
    }

@router.post("/mapping-insert", response_model=TransactionResponse)
def mapping_insert_transaction(
    request: MappingInsertRequest,
    db: Session = Depends(get_db)
):
    """
    Create a transaction record from a loan transaction.
    Maps loan_transaction data to transactions table.
    Sends contract signed email if to_emails provided.
    """
    # Get the loan transaction
    loan_transaction = db.query(LoanTransaction).filter(
        LoanTransaction.id == request.transaction_id
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
        account_no=request.account_no,
        status_approval=loan_transaction.status_approval,
        date_approved=loan_transaction.date_approved
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    # Send contract signed email
    if request.to_emails:
        try:
            email_service.send_contract_signed_email(
                borrower_name=loan_transaction.borrower,
                loan_id=loan_transaction.loan_id,
                amount=loan_transaction.loan_amount,
                account_no=request.account_no,
                to_emails=request.to_emails
            )
        except Exception as e:
            logging.warning("Contract email failed (transaction %s created): %s",
                            request.transaction_id, e)

    return new_transaction


@router.post("/mapping-insert-bulk", response_model=dict)
def mapping_insert_bulk_transactions(
    request: MappingInsertBulkRequest,
    db: Session = Depends(get_db)
):
    """
    Create multiple transaction records from loan transactions.
    Bulk mapping operation. Sends contract signed emails if to_emails provided.
    """
    created_count = 0
    skipped_count = 0
    created_ids = []
    emailed_count = 0
    
    for transaction_id in request.transaction_ids:
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
            account_no=request.account_no,
            status_approval=loan_transaction.status_approval,
            date_approved=loan_transaction.date_approved
        )
        
        db.add(new_transaction)
        db.flush()
        created_ids.append(new_transaction.id)
        created_count += 1

        # Send contract signed email
        if request.to_emails:
            try:
                email_service.send_contract_signed_email(
                    borrower_name=loan_transaction.borrower,
                    loan_id=loan_transaction.loan_id,
                    amount=loan_transaction.loan_amount,
                    account_no=request.account_no,
                    to_emails=request.to_emails
                )
                emailed_count += 1
            except Exception as e:
                logging.warning("Contract email failed (transaction %s): %s",
                                transaction_id, e)
    
    db.commit()
    
    return {
        "success": True,
        "created_count": created_count,
        "skipped_count": skipped_count,
        "emailed_count": emailed_count,
        "created_transaction_ids": created_ids
    }