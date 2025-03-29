from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.bank import BankResponse, BankCreate
from app.services.auth import AuthService

router = APIRouter(
    prefix="/bank",
    tags=["Bank Details"]
)

@router.post("/", response_model=BankResponse)
def create_bank_details(bank_data: BankCreate, db: Session = Depends(get_db)):
    # Implement bank details creation
    pass