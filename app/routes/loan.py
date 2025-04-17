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
