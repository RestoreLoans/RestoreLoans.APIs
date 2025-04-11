from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.bank import BankDetail, AccountType
from ..schemas.bank import BankDetailCreate, BankDetailResponse

router = APIRouter(
    prefix="/bank-details",
    tags=["Bank Details"]
)

@router.post("/", response_model=BankDetailResponse, status_code=status.HTTP_201_CREATED)
def create_bank_detail(bank_data: BankDetailCreate, db: Session = Depends(get_db)):
    # Check if a bank detail with the same account number already exists
    existing_bank_detail = db.query(BankDetail).filter(BankDetail.account_number == bank_data.account_number).first()
    if existing_bank_detail:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bank detail with this account number already exists."
        )

    # Create a new bank detail instance
    new_bank_detail = BankDetail(
        user_id=bank_data.user_id,
        bank_name=bank_data.bank_name,
        branch_name=bank_data.branch_name,
        branch_code=bank_data.branch_code,
        account_holder_name=bank_data.account_holder_name,
        account_number=bank_data.account_number,
        account_type=bank_data.account_type
    )

    # Add the bank detail to the database
    db.add(new_bank_detail)
    db.commit()
    db.refresh(new_bank_detail)  # Refresh to get the updated data from the database

    return new_bank_detail