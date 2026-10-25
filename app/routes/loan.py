from fastapi import APIRouter, Depends,UploadFile, HTTPException, status, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.loan import Loan
from app.models.user import User
from app.models.transaction import Transaction
from app.models.loan_application import LoanApplication, STATUS_PENDING_APPROVAL
from datetime import datetime as _dt, timezone as _tz
from app.schemas.loan import LoanCreate, LoanResponse
from app.schemas.loan_dashboard import LoanDashboardResponse, UserStats, LoanDashboardLoan, PaymentHistoryItem
from google.cloud import storage
import os
from datetime import datetime
import logging
from app.services.email_service import email_service
from app.utils.gcs_credentials import configure_gcs_credentials


configure_gcs_credentials()
router = APIRouter(
    prefix="/loans",
    tags=["Loans"]
)
BUCKET_NAME = "restoreloans"


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
    id_document: UploadFile = File(None),
    bank_statement: UploadFile = File(None),
    proof_of_residence: UploadFile = File(None), db: Session = Depends(get_db)):
    # Normalize loan_type so responses serialize correctly (schema uses a
    # lowercase enum while the DB column is a free-form string).
    loan_type = loan_type.strip().lower()

    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID"

        )

    # Most recent prior loan for this user, used to reuse documents when the
    # applicant's documents are still recent (< 3 months) and uploads are disabled.
    existing_loan = (
        db.query(Loan)
        .filter(Loan.user_id == user_id)
        .order_by(Loan.id.desc())
        .first()
    )
    # Read document bytes upfront (needed for both GCS and email attachments)
    doc_files = [
        ("id_document", id_document),
        ("bank_statement", bank_statement),
        ("proof_of_residence", proof_of_residence),
    ]
    doc_bytes = {}
    for key, upload in doc_files:
        if upload is None:
            continue
        upload.file.seek(0)
        doc_bytes[key] = upload.file.read()
        upload.file.seek(0)

    # Try GCS uploads (best effort — don't crash loan creation if GCS fails).
    # When the applicant's documents are still recent (< 3 months) the upload
    # controls are disabled, so we reuse the most recent stored document paths
    # instead of requiring a fresh upload.
    id_path = None
    bank_path = None
    proof_path = None
    if id_document is not None:
        try:
            id_path = upload_to_gcs(id_document, "id_documents", user_id)
        except Exception as e:
            logging.warning("GCS upload failed for id_document: %s", e)
    elif existing_loan and getattr(existing_loan, "id_path", None):
        id_path = existing_loan.id_path
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ID document is required")

    if bank_statement is not None:
        try:
            bank_path = upload_to_gcs(bank_statement, "bank_statements", user_id)
        except Exception as e:
            logging.warning("GCS upload failed for bank_statement: %s", e)
    elif existing_loan and getattr(existing_loan, "bank_path", None):
        bank_path = existing_loan.bank_path
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Bank statement is required")

    if proof_of_residence is not None:
        try:
            proof_path = upload_to_gcs(proof_of_residence, "residences", user_id)
        except Exception as e:
            logging.warning("GCS upload failed for proof_of_residence: %s", e)
    elif existing_loan and getattr(existing_loan, "proof_of_residence_path", None):
        proof_path = existing_loan.proof_of_residence_path
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Proof of residence is required")

    # Create and save the loan
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
        id_path=id_path,
        bank_path=bank_path,
        proof_of_residence_path=proof_path,
    )
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)

    # Every new application starts as "Pending Approval" until a staff member
    # (admin/manager) reviews it. Stored separately from the legacy enum column.
    now = _dt.now(_tz.utc).replace(tzinfo=None)
    db.add(
        LoanApplication(
            loan_id=new_loan.id,
            status=STATUS_PENDING_APPROVAL,
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()

    borrower_name = f"{user.first_name} {user.last_name}".strip()

    # 1. Send acknowledgement email to the loan applicant.
    try:
        if user.email:
            email_service.send_loan_application_email(
                borrower_name=borrower_name,
                loan_id=new_loan.id,
                amount=new_loan.loan_amount,
                to_emails=[user.email],
            )
    except Exception as e:
        logging.exception("Failed to send applicant acknowledgement email for loan %s",
                          new_loan.id)

    # 2. Send application with documents to applicants@restoreloans.co.za
    #    (backend has direct access to uploaded file bytes — more reliable than
    #    re-downloading from GCS on the frontend).
    docs_email_sent = False
    try:
        import urllib.request

        def _download(url):
            try:
                with urllib.request.urlopen(url, timeout=30) as resp:
                    return resp.read()
            except Exception:
                return None

        id_bytes = doc_bytes.get("id_document")
        bank_bytes = doc_bytes.get("bank_statement")
        residence_bytes = doc_bytes.get("proof_of_residence")

        if id_bytes is None and id_path:
            id_bytes = _download(id_path)
        if bank_bytes is None and bank_path:
            bank_bytes = _download(bank_path)
        if residence_bytes is None and proof_path:
            residence_bytes = _download(proof_path)

        attachments = []
        if id_bytes is not None:
            attachments.append((id_bytes, (id_document.filename if id_document else None) or (id_path.split("/")[-1] if id_path else "id_document")))
        if bank_bytes is not None:
            attachments.append((bank_bytes, (bank_statement.filename if bank_statement else None) or (bank_path.split("/")[-1] if bank_path else "bank_statement")))
        if residence_bytes is not None:
            attachments.append((residence_bytes, (proof_of_residence.filename if proof_of_residence else None) or (proof_path.split("/")[-1] if proof_path else "proof_of_residence")))
        email_service.send_application_with_docs_email(
            loan=new_loan,
            client=user,
            employer=getattr(user, "company", None),
            bank=getattr(user, "bank", None),
            to_emails=["applicants@restoreloans.co.za"],
            attachments=attachments,
        )
        docs_email_sent = True
    except Exception as e:
        logging.exception("Failed to send application email with docs for loan %s",
                          new_loan.id)

    # Persist the "sent" flag so the frontend's follow-up call to
    # /loan-transactions/send-application-docs-email becomes a no-op and cannot
    # produce a duplicate (attachment-less) "New Loan Application" email. The
    # flag is only set after the send actually succeeded.
    if docs_email_sent:
        try:
            new_loan.docs_email_sent = True
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error("Failed to persist docs email flag for loan %s: %s",
                          new_loan.id, e)

    return new_loan

@router.get("/", response_model=list[LoanResponse], status_code=status.HTTP_200_OK)
def get_all_loans(db: Session = Depends(get_db)):
    loans = db.query(Loan).all()
    app_statuses = {
        a.loan_id: a.status for a in db.query(LoanApplication).all()
    }
    result = []
    for loan in loans:
        status_value = app_statuses.get(loan.id) or _map_loan_status(loan.status)
        result.append(
            LoanResponse(
                loan_type=loan.loan_type,
                loan_amount=loan.loan_amount,
                interest_rate=loan.interest_rate,
                loan_term=loan.loan_term,
                monthly_installment=loan.monthly_installment,
                start_date=loan.start_date,
                end_date=loan.end_date,
                id_path=loan.id_path,
                bank_path=loan.bank_path,
                proof_of_residence_path=loan.proof_of_residence_path,
                id=loan.id,
                user_id=loan.user_id,
                status=status_value,
                created_at=loan.created_at,
            )
        )
    return result

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

    # Prefer the dedicated application status when present (new applications),
    # falling back to the legacy loan.status mapping for older records.
    application_status = {
        app.loan_id: app.status
        for app in db.query(LoanApplication)
        .filter(LoanApplication.loan_id.in_([loan.id for loan in loans] or [-1]))
        .all()
    }

    def _status_for(loan):
        return application_status.get(loan.id) or _map_loan_status(loan.status)

    total_loans = len(loans)
    mapped_statuses = [_status_for(loan) for loan in loans]
    active_loans = len(
        [
            status
            for status in mapped_statuses
            if status in {"disbursed", "pending", "pending_approval", "approved"}
        ]
    )
    completed_loans = len(
        [status for status in mapped_statuses if status in {"completed", "paid"}]
    )
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

        account_number = None
        for transaction in sorted(
            loan_transactions,
            key=lambda item: item.payment_date or item.date_time or datetime.min
        ):
            if transaction.account_number:
                account_number = transaction.account_number

        remaining_months = max((loan.loan_term or 0) - paid_months, 0)
        # Outstanding Balance must include interest, so it is the repayments
        # still outstanding: the stored installment already includes interest
        # & fees (the quote payment). This matches the downloadable statement,
        # which multiplies the installment by the remaining months.
        outstanding_balance = max(
            (loan.monthly_installment or 0) * remaining_months, 0
        )

        user_loans.append(
            LoanDashboardLoan(
                id=_format_loan_id(loan.id),
                customerName=user_name,
                loanAmount=loan.loan_amount,
                loanTerm=loan.loan_term,
                monthlyPayment=loan.monthly_installment,
                interestRate=loan.interest_rate,
                status=_status_for(loan),
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
    configure_gcs_credentials()
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    # Generate unique filename
    unique_filename = f"{folder}/{uid}_{file.filename}"

    blob = bucket.blob(unique_filename)
    blob.upload_from_file(file.file, content_type=file.content_type)

    # Make file public
    #blob.make_public()

    return f"https://storage.googleapis.com/{bucket.name}/{unique_filename}"