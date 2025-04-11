from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.loan import LoanResponse, LoanCreate
from ..services.auth import AuthService
from fastapi import HTTPException, status
from ..models.loan import Loan

router = APIRouter(
    prefix="/loans",
    tags=["Loans"]
)

@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(loan_data: LoanCreate, db: Session = Depends(get_db)):
    # Create a new loan instance
    new_loan = Loan(
        user_id=loan_data.user_id,
        loan_type=loan_data.loan_type,
        loan_amount=loan_data.loan_amount,
        interest_rate=loan_data.interest_rate,
        loan_term=loan_data.loan_term,
        monthly_installment=loan_data.monthly_installment,
        start_date=loan_data.start_date,
        end_date=loan_data.end_date,
        status="active"  # Default status
    )

    # Add the loan to the database
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)  # Refresh to get the updated data from the database

    return new_loan