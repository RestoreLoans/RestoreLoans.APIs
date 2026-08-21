from fastapi import APIRouter, Depends,UploadFile, HTTPException, status, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.loan import Loan
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.loan import LoanCreate, LoanResponse
from app.schemas.loan_dashboard import LoanDashboardResponse, UserStats, LoanDashboardLoan, PaymentHistoryItem
from google.cloud import storage
import os
from datetime import datetime
import logging
from app.services.email_service import email_service


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "app/utils/google.json"
router = APIRouter(
    prefix="/loans",
    tags=["Loans"]
)
BUCKET_NAME = "restoreloans"
SERVICE_ACCOUNT_FILE = "app/utils/google_service_account.json"


def _format_loan_id(loan_id: int) -> str:
    return f"LOAN{loan_id:03d}"


def _format_payment_id(payment_id: int) -> str:
    return f"PAY{payment_id:03d}"


def _map_loan_status(status_value: str) -> str:
    if not status_value:
        return "pending"
    if hasattr(status_value, "value"):
        normalized = str(status_value.value).lower()
    else:
        normalized = str(status_value).lower()
    if normalized == "active":
        return "disbursed"
    if normalized == "paid":
        return "completed"
    if normalized == "default":
        return "rejected"
    return normalized


def _get_application_date(loan: Loan):
    created_at = getattr(loan, "created_at", None)
    if isinstance(created_at, datetime):
        return created_at.date()
    return created_at


def _parse_interest_rate(value: str) -> float:
    cleaned = str(value).strip().replace("%", "").replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid interest_rate: '{value}'"
        )


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(  loan_type: str = Form(...),
    loan_amount: float = Form(...),
    interest_rate: str = Form(...),
    loan_term: int = Form(...),
    monthly_installment: float = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    user_id: int = Form(...),
    id_document: UploadFile = File(...),
    bank_statement: UploadFile = File(...),
    proof_of_residence: UploadFile = File(...), db: Session = Depends(get_db)):
    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID"

        )

    # Create a new loan instance
    new_loan = Loan(
        user_id=user_id,
        loan_type=loan_type,
        loan_amount=loan_amount,
        interest_rate=_parse_interest_rate(interest_rate),
        loan_term=loan_term,
        monthly_installment=monthly_installment,
        start_date=start_date,
        end_date=end_date,
        status="active",
        id_path =upload_to_gcs(id_document, "id_documents",user_id),
        bank_path=upload_to_gcs(bank_statement, "bank_statements",user_id), 
        proof_of_residence_path = upload_to_gcs(proof_of_residence, "residences",user_id)

    )

    # Add the loan to the database
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)
    # Send application notification email (do not block on email failures)
    try:
        borrower_name = f"{user.first_name} {user.last_name}".strip()
        # Best-effort send; log any failures
        email_service.send_loan_application_email(
            borrower_name=borrower_name,
            loan_id=new_loan.id,
            amount=new_loan.loan_amount,
            to_emails=[user.email] if getattr(user, 'email', None) else []
        )
    except Exception as e:
        logging.error("Failed to send loan application email for loan %s: %s", new_loan.id, e)
    return new_loan

@router.get("/", response_model=list[LoanResponse], status_code=status.HTTP_200_OK)
def get_all_loans(db: Session = Depends(get_db)):
    loans = db.query(Loan).all()
    return loans

@router.get("/{loan_id}", response_model=LoanResponse, status_code=status.HTTP_200_OK)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with ID {loan_id} does not exist."
        )
    return loan
@router.get("/by-user-id/{user_id}", response_model=LoanResponse, status_code=status.HTTP_200_OK)
def get_loan_by_user(user_id: int, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.user_id == user_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with ID {user_id} does not exist."
        )
    return loan


@router.get("/dashboard/{user_id}", response_model=LoanDashboardResponse, status_code=status.HTTP_200_OK)
def get_loan_dashboard(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    loans = db.query(Loan).filter(Loan.user_id == user_id).all()
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()

    total_loans = len(loans)
    mapped_statuses = [_map_loan_status(loan.status) for loan in loans]
    active_loans = len([status for status in mapped_statuses if status in {"disbursed", "pending", "pending_approval"}])
    completed_loans = len([status for status in mapped_statuses if status == "completed"])
    total_borrowed = sum(loan.loan_amount for loan in loans)

    user_name = f"{user.first_name} {user.last_name}".strip()

    payment_history = []
    for transaction in sorted(
        transactions,
        key=lambda item: item.payment_date or item.date_time or datetime.min
    ):
        payment_history.append(
            PaymentHistoryItem(
                loanId=_format_loan_id(transaction.loan_id),
                paymentId=_format_payment_id(transaction.id),
                paymentDate=transaction.payment_date or transaction.date_time,
                amount=transaction.amount or 0,
                paymentMethod=transaction.transaction_type,
                status=transaction.status
            )
        )

    user_loans = []
    for loan in loans:
        loan_transactions = [t for t in transactions if t.loan_id == loan.id]
        completed_payments = [
            t for t in loan_transactions
            if (t.status or "").lower() in {"completed", "paid", "success"}
        ]
        paid_months = len(completed_payments)
        if paid_months == 0:
            paid_months = len([t for t in loan_transactions if t.payment_date or t.date_time])

        payments_total = sum(
            (t.debit if t.debit is not None else (t.amount or 0)) for t in completed_payments
        )

        last_balance = None
        account_number = None
        for transaction in sorted(
            loan_transactions,
            key=lambda item: item.payment_date or item.date_time or datetime.min
        ):
            if transaction.balance is not None:
                last_balance = transaction.balance
            if transaction.account_number:
                account_number = transaction.account_number

        outstanding_balance = last_balance if last_balance is not None else max(loan.loan_amount - payments_total, 0)
        remaining_months = max((loan.loan_term or 0) - paid_months, 0)

        user_loans.append(
            LoanDashboardLoan(
                id=_format_loan_id(loan.id),
                customerName=user_name,
                loanAmount=loan.loan_amount,
                loanTerm=loan.loan_term,
                monthlyPayment=loan.monthly_installment,
                interestRate=loan.interest_rate,
                status=_map_loan_status(loan.status),
                disburseDate=loan.start_date,
                applicationDate=_get_application_date(loan),
                outstandingBalance=outstanding_balance,
                paidMonths=paid_months,
                remainingMonths=remaining_months,
                accountNumber=account_number,
                decisionDate=None,
                decisionReason=None
            )
        )

    return LoanDashboardResponse(
        userName=user_name,
        userStats=UserStats(
            totalLoans=total_loans,
            activeLoans=active_loans,
            completedLoans=completed_loans,
            totalBorrowed=total_borrowed
        ),
        userLoans=user_loans,
        paymentHistory=payment_history
    )


@router.put("/{loan_id}", response_model=LoanResponse, status_code=status.HTTP_200_OK)
def update_loan(loan_id: int, loan_data: dict, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with ID {loan_id} does not exist."
        )

    # Update loan fields
    for key, value in loan_data.dict(exclude_unset=True).items():
        setattr(loan, key, value)

    db.commit()
    db.refresh(loan)
    return loan

@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with ID {loan_id} does not exist."
        )

    db.delete(loan)
    db.commit()
    return None
def upload_to_gcs(file: UploadFile, folder: str = "loans", uid:str="") -> str:
    """Upload file to GCS and return its public URL."""
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    # Generate unique filename
    unique_filename = f"{folder}/{uid}_{file.filename}"

    blob = bucket.blob(unique_filename)
    blob.upload_from_file(file.file, content_type=file.content_type)

    # Make file public
    #blob.make_public()

    return f"https://storage.googleapis.com/{bucket.name}/{unique_filename}"