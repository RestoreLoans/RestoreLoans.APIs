from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.loan import LoanResponse, LoanCreate
from app.services.auth import AuthService

router = APIRouter(
    prefix="/loans",
    tags=["Loans"]
)

@router.post("/", response_model=LoanResponse)
def create_loan(loan_data: LoanCreate, db: Session = Depends(get_db)):
    # Implement loan creation
    pass