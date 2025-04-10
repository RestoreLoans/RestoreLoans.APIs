from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.bank import BankResponse, BankCreate
from app.services.auth import AuthService
from fastapi import HTTPException, status
from app.models.user import User  # Assuming User is the SQLAlchemy model for users

router = APIRouter(
    prefix="/bank",
    tags=["Bank Details"]
)

@router.post("/", response_model=BankResponse)
def create_bank_details(bank_data: BankCreate, db: Session = Depends(get_db)):
    # Check if bank details with the same account number already exist
    existing_bank = db.query(Bank).filter(Bank.account_number == bank_data.account_number).first()
    if existing_bank:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bank details with this account number already exist."
        )

    # Create a new bank details instance
    new_bank = Bank(
        account_number=bank_data.account_number,
        bank_name=bank_data.bank_name,
        branch_name=bank_data.branch_name,
        ifsc_code=bank_data.ifsc_code,
        user_id=bank_data.user_id  # Assuming this links the bank details to a user
    )

    # Add the bank details to the database
    db.add(new_bank)
    db.commit()
    db.refresh(new_bank)  # Refresh to get the updated data from the database

    return new_bank