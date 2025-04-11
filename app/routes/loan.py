from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.loan import Loan
from app.models.user import User
from app.schemas.loan import LoanCreate, LoanResponse

router = APIRouter(
    prefix="/loans",
    tags=["Loans"]
)

@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(loan_data: LoanCreate, db: Session = Depends(get_db)):
    # Check if the user exists
    user = db.query(User).filter(User.id == loan_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {loan_data.user_id} does not exist."
        )

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
        status="active"
    )

    # Add the loan to the database
    db.add(new_loan)
    db.commit()
    db.refresh(new_loan)

    return new_loan