from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.loan import LoanResponse, LoanCreate
from app.services.auth import AuthService
from datetime import datetime
from app.models.loan import Loan  # Assuming Loan is the SQLAlchemy model for loans
from fastapi import HTTPException, status

router = APIRouter(
    prefix="/loans",
    tags=["Loans"]
)

@router.post("/", response_model=LoanResponse)
def create_loan(loan_data: LoanCreate, db: Session = Depends(get_db)):
    # Check if a loan with the same identifier already exists (if applicable)
    existing_loan = db.query(Loan).filter(Loan.id == loan_data.id).first()
    if existing_loan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A loan with this ID already exists."
        )

    # Create a new loan instance
    new_loan = Loan(
    id=loan_data.id,    
    user_id=loan_data.user_id,  # Maps to the `user_id` field in the Loan model
    loan_type=loan_data.loan_type,  # Maps to the `loan_type` field in the Loan model
    loan_amount=loan_data.loan_amount,  # Maps to the `loan_amount` field in the Loan model
    interest_rate=loan_data.interest_rate,  # Maps to the `interest_rate` field in the Loan model
    loan_term=loan_data.loan_term,  # Maps to the `loan_term` field in the Loan model
    monthly_installment=loan_data.monthly_installment,  # Maps to the `monthly_installment` field in the Loan model
    start_date=loan_data.start_date,  # Maps to the `start_date` field in the Loan model
    end_date=loan_data.end_date,  # Maps to the `end_date` field in the Loan model
    status=loan_data.status or "active"  # Defaults to "active" if not provided
)

    # Add the loan to the database
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)  # Refresh to get the updated data from the database

    return new_loan