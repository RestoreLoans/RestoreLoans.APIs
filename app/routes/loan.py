from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.loan import LoanResponse, LoanCreate
from ..services.auth import AuthService

router = APIRouter(
    prefix="/loans",
    tags=["Loans"]
)

@router.post("/", response_model=LoanResponse)
def create_loan(loan_data: LoanCreate, db: Session = Depends(get_db)):
    # Implement loan creation
    pass