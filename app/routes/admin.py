from datetime import datetime, timezone, timedelta
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.loan import Loan
from app.models.document import Document
from app.models.loan_application import (
    LoanApplication,
    VALID_APPLICATION_STATUSES,
    STATUS_PENDING_APPROVAL,
)
from app.models.document_request import DocumentRequest
import secrets
from app.models.user_role_assignment import ROLE_ADMIN, ROLE_MANAGER, ROLE_VIEWER
from app.schemas.admin import (
    UpdateApplicationStatusRequest,
    AssignRoleRequest,
)
from app.services.roles import RoleService
from app.services.email_service import email_service

router = APIRouter(prefix="/admin", tags=["Admin"])

STAFF_ROLES = {ROLE_ADMIN, ROLE_MANAGER, ROLE_VIEWER}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _format_loan_id(loan_id: int) -> str:
    return f"LOAN{loan_id:03d}"


def _map_legacy_status(status_value) -> str:
    if not status_value:
        return "pending"
    normalized = (
        str(status_value.value).lower()
        if hasattr(status_value, "value")
        else str(status_value).lower()
    )
    if normalized == "active":
        return "disbursed"
    if normalized == "paid":
        return "completed"
    if normalized == "default":
        return "defaulted"
    return normalized


def _resolve_status(loan: Loan, app: Optional[LoanApplication]) -> str:
    if app and app.status:
        return app.status
    return _map_legacy_status(loan.status)


def _documents_for_loan(loan: Loan, db: Session) -> List[dict]:
    docs = []
    if getattr(loan, "id_path", None):
        docs.append({"name": "ID Document", "url": loan.id_path})
    if getattr(loan, "bank_path", None):
        docs.append({"name": "Bank Statement", "url": loan.bank_path})
    if getattr(loan, "proof_of_residence_path", None):
        docs.append({"name": "Proof of Residence", "url": loan.proof_of_residence_path})
    try:
        rows = db.query(Document).filter(Document.loan_id == loan.id).all()
        for row in rows:
            docs.append({"name": row.document_name or row.file_name, "url": row.file_path})
    except Exception:
        pass
    return docs


def _application_payload(loan: Loan, user: Optional[User], app: Optional[LoanApplication], db: Session) -> dict:
    company = getattr(user, "company", None) if user else None
    outstanding_balance = None
    try:
        total_paid = 0.0
        from app.models.transaction import Transaction

        txns = db.query(Transaction).filter(Transaction.loan_id == loan.id).all()
        for t in txns:
            amt = getattr(t, "amount", None) or getattr(t, "transaction_amount", None)
            if amt is not None:
                try:
                    total_paid += float(amt)
                except Exception:
                    pass
        principal = float(loan.loan_amount or 0)
        outstanding_balance = max(0.0, principal - total_paid)
    except Exception:
        outstanding_balance = loan.loan_amount
    return {
        "id": _format_loan_id(loan.id),
        "loanId": loan.id,
        "userId": loan.user_id,
        "firstName": user.first_name if user else None,
        "lastName": user.last_name if user else None,
        "customerName": f"{user.first_name} {user.last_name}".strip() if user else "",
        "surname": user.last_name if user else None,
        "email": user.email if user else None,
        "phone": user.phone_number if user else None,
        "idNumber": user.id_number if user else None,
        "loanAmount": loan.loan_amount,
        "amount": loan.loan_amount,
        "loanTerm": loan.loan_term,
        "loan_period": loan.loan_term,
        "monthlyInstallment": loan.monthly_installment,
        "interestRate": loan.interest_rate,
        "loanType": loan.loan_type,
        "loan_type": loan.loan_type,
        "status": _resolve_status(loan, app),
        "balance": outstanding_balance,
        "outstandingBalance": outstanding_balance,
        "applicationDate": loan.created_at.isoformat() if loan.created_at else None,
        "applied_at": loan.created_at.isoformat() if loan.created_at else None,
        "created_at": loan.created_at.isoformat() if loan.created_at else None,
        "disburseDate": loan.start_date.isoformat() if loan.start_date else None,
        "start_date": loan.start_date.isoformat() if loan.start_date else None,
        "endDate": loan.end_date.isoformat() if loan.end_date else None,
        "end_date": loan.end_date.isoformat() if loan.end_date else None,
        "employmentStatus": getattr(company, "employment_status", None) if company else None,
        "employerName": company.name if company else None,
        "decidedBy": app.decided_by if app else None,
        "decidedAt": app.decided_at.isoformat() if app and app.decided_at else None,
        "notes": app.notes if app else None,
        "documents": _documents_for_loan(loan, db),
    }


@router.get("/me")
def admin_me(email: str, db: Session = Depends(get_db)):
    role = RoleService.get_role_by_email(db, email)
    return {
        "email": email,
        "role": role,
        "isStaff": role in STAFF_ROLES,
        "permissions": {
            "view": role in STAFF_ROLES,
            "manage": role == ROLE_ADMIN,
            "review": role in {ROLE_ADMIN, ROLE_MANAGER},
        },
    }


@router.get("/applications")
def list_applications(email: str = None, db: Session = Depends(get_db), all_loans: bool = True):
    if email:
        RoleService.require_role(db, email, STAFF_ROLES)
    else:
        # Allow loading all loans for admin dashboard if role check not provided
        pass

    loans = db.query(Loan).order_by(Loan.id.desc()).all()
    users = {u.id: u for u in db.query(User).all()}
    apps = {
        a.loan_id: a
        for a in db.query(LoanApplication).all()
    }

    data = [
        _application_payload(loan, users.get(loan.user_id), apps.get(loan.id), db)
        for loan in loans
    ]
    return {"role": RoleService.get_role_by_email(db, email) if email else "admin", "applications": data}


@router.get("/applications/{loan_id}")
def get_application(loan_id: int, email: str, db: Session = Depends(get_db)):
    RoleService.require_role(db, email, STAFF_ROLES)

    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found."
        )
    user = db.query(User).filter(User.id == loan.user_id).first()
    app = db.query(LoanApplication).filter(LoanApplication.loan_id == loan.id).first()
    return _application_payload(loan, user, app, db)


@router.post("/applications/{loan_id}/status")
def update_application_status(
    loan_id: int, body: UpdateApplicationStatusRequest, db: Session = Depends(get_db)
):
    role = RoleService.require_role(db, body.email, {ROLE_ADMIN, ROLE_MANAGER})

    new_status = (body.status or "").strip().lower()
    if new_status not in VALID_APPLICATION_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed: {', '.join(sorted(VALID_APPLICATION_STATUSES))}",
        )

    if not RoleService.can_set_status(role, new_status):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your role cannot set this application status.",
        )

    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found."
        )

    app = db.query(LoanApplication).filter(LoanApplication.loan_id == loan.id).first()
    if not app:
        # Legacy loans created before the LoanApplication table existed may not
        # have a record yet. Create one on demand so status updates (and the
        # resulting email notifications) work for every loan.
        now = _utcnow()
        app = LoanApplication(
            loan_id=loan.id,
            status=STATUS_PENDING_APPROVAL,
            created_at=now,
            updated_at=now,
        )
        db.add(app)
        db.flush()

    app.status = new_status
    app.decided_by = body.email
    app.decided_at = _utcnow()
    if body.notes is not None:
        app.notes = body.notes
    app.updated_at = _utcnow()
    db.commit()
    db.refresh(app)

    user = db.query(User).filter(User.id == loan.user_id).first()
    try:
        if user and user.email:
            borrower_name = f"{user.first_name} {user.last_name}".strip() or user.email
            if new_status == "approved":
                email_service.send_loan_approval_email(
                    borrower_name=borrower_name,
                    loan_id=loan.id,
                    amount=loan.loan_amount or 0,
                    account_no=getattr(getattr(user, "bank", None), "account_number", None) or "N/A",
                    to_emails=[user.email],
                )
            elif new_status == "rejected":
                email_service.send_loan_rejection_email(
                    borrower_name=borrower_name,
                    loan_id=loan.id,
                    reason=body.notes or "Your application was not approved at this time.",
                    to_emails=[user.email],
                )
            elif new_status in {"disbursed", "completed"}:
                try:
                    email_service.send_contract_signed_email(
                        borrower_name=borrower_name,
                        loan_id=loan.id,
                        amount=loan.loan_amount or 0,
                        account_no=getattr(getattr(user, "bank", None), "account_number", None) or "N/A",
                        to_emails=[user.email],
                    )
                except Exception:
                    email_service.send_custom_loan_email(
                        borrower_name=borrower_name,
                        loan_id=loan.id,
                        amount=loan.loan_amount or 0,
                        status=new_status,
                        message=body.notes or f"Your loan status has been updated to {new_status.replace('_', ' ')}.",
                        to_emails=[user.email],
                    )
            else:
                email_service.send_custom_loan_email(
                    borrower_name=borrower_name,
                    loan_id=loan.id,
                    amount=loan.loan_amount or 0,
                    status=new_status,
                    message=body.notes or f"Your loan application status has been updated to {new_status.replace('_', ' ')}.",
                    to_emails=[user.email],
                )
    except Exception:
        import logging

        logging.exception("Failed to send status update email for loan %s", loan.id)
    return _application_payload(loan, user, app, db)


@router.post("/applications/{loan_id}/request-document")
def request_document_update(
    loan_id: int,
    body: dict,
    db: Session = Depends(get_db),
):
    email = body.get("email")
    role = RoleService.require_role(db, email, {ROLE_ADMIN, ROLE_MANAGER})
    doc_type = (body.get("document_type") or "").strip()
    reason = (body.get("reason") or "").strip()
    if doc_type not in {"id_document", "bank_statement", "proof_of_residence"}:
        raise HTTPException(status_code=400, detail="Invalid document type.")
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Application not found.")
    user = db.query(User).filter(User.id == loan.user_id).first()
    if not user or not user.email:
        raise HTTPException(status_code=404, detail="Applicant email not found.")

    token = secrets.token_urlsafe(32)
    req = DocumentRequest(
        loan_id=loan.id,
        document_type=doc_type,
        requested_by=email,
        reason=reason or "Document requires correction.",
        token=token,
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    frontend = os.getenv("FRONTEND_URL", "https://restoreloans.co.za")
    upload_link = f"{frontend}/upload-document?token={token}&loan_id={loan.id}&document_type={doc_type}"

    doc_label = doc_type.replace("_", " ").title()
    subject = f"Document Update Required - Loan #{loan.id}"
    body_html = f"""
    <html><body style="font-family: Arial, sans-serif; padding: 20px;">
      <h2>Document Update Required</h2>
      <p>Dear {user.first_name} {user.last_name},</p>
      <p>We need an updated copy of your <strong>{doc_label}</strong> for loan application #{loan.id}.</p>
      <p><strong>Reason:</strong> {reason or 'The submitted document is incorrect, invalid, or expired.'}</p>
      <p>Please upload the replacement document using this secure link:</p>
      <p><a href="{upload_link}">{upload_link}</a></p>
      <p>You only need to upload the requested document; previously approved documents remain valid.</p>
      <p>Best regards,<br>RestoreLoans Team</p>
    </body></html>
    """
    try:
        email_service.send_email([user.email], subject, body_html, is_html=True)
    except Exception:
        logging.exception("Failed to send document request email for loan %s", loan.id)

    return {
        "message": "Document update requested.",
        "request_id": req.id,
        "token": token,
        "upload_link": upload_link,
    }


@router.get("/applications/{loan_id}/document-requests")
def list_document_requests(loan_id: int, email: str, db: Session = Depends(get_db)):
    RoleService.require_role(db, email, STAFF_ROLES)
    reqs = db.query(DocumentRequest).filter(DocumentRequest.loan_id == loan_id).order_by(DocumentRequest.id.desc()).all()
    return {
        "requests": [
            {
                "id": r.id,
                "document_type": r.document_type,
                "requested_by": r.requested_by,
                "reason": r.reason,
                "status": r.status,
                "requested_at": r.requested_at.isoformat() if r.requested_at else None,
                "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                "reviewer_email": r.reviewer_email,
                "review_outcome": r.review_outcome,
                "uploaded_file_path": r.uploaded_file_path,
            }
            for r in reqs
        ]
    }


@router.post("/document-requests/{request_id}/review")
def review_document_request(request_id: int, body: dict, db: Session = Depends(get_db)):
    email = body.get("email")
    RoleService.require_role(db, email, {ROLE_ADMIN, ROLE_MANAGER})
    req = db.query(DocumentRequest).filter(DocumentRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Document request not found.")
    new_status = (body.get("status") or "").strip().lower()
    if new_status not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Status must be approved or rejected.")
    req.status = new_status
    req.reviewer_email = email
    req.reviewed_at = _utcnow()
    req.review_outcome = body.get("notes")
    # Update loan document path if approved and uploaded
    if new_status == "approved" and req.uploaded_file_path:
        loan = db.query(Loan).filter(Loan.id == req.loan_id).first()
        if loan:
            if req.document_type == "id_document":
                loan.id_path = req.uploaded_file_path
            elif req.document_type == "bank_statement":
                loan.bank_path = req.uploaded_file_path
            elif req.document_type == "proof_of_residence":
                loan.proof_of_residence_path = req.uploaded_file_path
    db.commit()
    return {"message": f"Document request {new_status}."}

@router.delete("/applications/{loan_id}", status_code=status.HTTP_200_OK)
def delete_application(loan_id: int, email: str, db: Session = Depends(get_db)):
    RoleService.require_role(db, email, {ROLE_ADMIN})

    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found."
        )
    db.query(LoanApplication).filter(LoanApplication.loan_id == loan.id).delete(
        synchronize_session=False
    )
    db.delete(loan)
    db.commit()
    return {"message": f"Application {_format_loan_id(loan_id)} deleted."}


@router.get("/logins")
def list_user_logins(email: str, db: Session = Depends(get_db)):
    RoleService.require_role(db, email, STAFF_ROLES)
    users = db.query(User).order_by(User.id.desc()).all()
    data = []
    for u in users:
        data.append({
            "id": u.id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "is_active": u.is_active,
            "failed_login_attempts": getattr(u, "failed_login_attempts", 0) or 0,
            "locked_until": u.locked_until.isoformat() if getattr(u, "locked_until", None) else None,
            "last_login": u.last_login.isoformat() if getattr(u, "last_login", None) else None,
            "created_at": u.created_at.isoformat() if hasattr(u.created_at, "isoformat") else str(u.created_at),
            "is_locked": bool(getattr(u, "locked_until", None) and u.locked_until and u.locked_until > _utcnow()),
        })
    return {"logins": data}


@router.post("/users/{user_id}/unlock")
def unlock_user(user_id: int, email: str, db: Session = Depends(get_db)):
    RoleService.require_role(db, email, {ROLE_ADMIN})
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    u.failed_login_attempts = 0
    u.locked_until = None
    db.commit()
    return {"message": f"User {u.email} unlocked."}


@router.post("/users/{user_id}/lock")
def lock_user(user_id: int, email: str, db: Session = Depends(get_db)):
    RoleService.require_role(db, email, {ROLE_ADMIN})
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    u.locked_until = _utcnow() + timedelta(hours=24)
    db.commit()
    return {"message": f"User {u.email} locked."}

@router.get("/staff")
def list_staff(email: str, db: Session = Depends(get_db)):
    RoleService.require_role(db, email, {ROLE_ADMIN})
    return {"staff": RoleService.list_staff(db)}


@router.post("/staff/role")
def assign_role(body: AssignRoleRequest, db: Session = Depends(get_db)):
    RoleService.require_role(db, body.email, {ROLE_ADMIN})
    target = db.query(User).filter(User.email == body.target_email.strip().lower()).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    role = RoleService.set_role(db, target, body.role)
    return {"message": f"{target.email} is now '{role}'.", "role": role}
