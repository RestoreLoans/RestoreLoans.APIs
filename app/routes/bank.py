from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.bank import BankDetail
from app.schemas.bank import BankDetailCreate, BankDetailResponse, BankDetailUpdate

router = APIRouter(
    prefix="/bank-details",
    tags=["Bank Details"]
)

# Create a new bank detail
@router.post("/", response_model=BankDetailResponse, status_code=status.HTTP_201_CREATED)
def create_bank_detail(bank_data: BankDetailCreate, db: Session = Depends(get_db)):
    existing_bank_detail = db.query(BankDetail).filter(BankDetail.account_number == bank_data.account_number).first()
    if existing_bank_detail:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bank detail with this account number already exists."
        )

    new_bank_detail = BankDetail(
        user_id=bank_data.user_id,
        bank_name=bank_data.bank_name,
        branch_name=bank_data.branch_name,
        branch_code=bank_data.branch_code,
        account_holder_name=bank_data.account_holder_name,
        account_number=bank_data.account_number,
        account_type=bank_data.account_type
    )

    db.add(new_bank_detail)
    db.commit()
    db.refresh(new_bank_detail)

    return new_bank_detail

# Retrieve all bank details
@router.get("/", response_model=list[BankDetailResponse])
def get_all_bank_details(db: Session = Depends(get_db)):
    return db.query(BankDetail).all()

# Retrieve a single bank detail by ID
@router.get("/{bank_detail_id}", response_model=BankDetailResponse)
def get_bank_detail(bank_detail_id: int, db: Session = Depends(get_db)):
    bank_detail = db.query(BankDetail).filter(BankDetail.id == bank_detail_id).first()
    if not bank_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank detail not found."
        )
    return bank_detail

# Update a bank detail
@router.put("/{bank_detail_id}", response_model=BankDetailResponse)
def update_bank_detail(bank_detail_id: int, bank_data: BankDetailUpdate, db: Session = Depends(get_db)):
    bank_detail = db.query(BankDetail).filter(BankDetail.id == bank_detail_id).first()
    if not bank_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank detail not found."
        )

    for key, value in bank_data.dict(exclude_unset=True).items():
        setattr(bank_detail, key, value)

    db.commit()
    db.refresh(bank_detail)

    return bank_detail

# Delete a bank detail
@router.delete("/{bank_detail_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bank_detail(bank_detail_id: int, db: Session = Depends(get_db)):
    bank_detail = db.query(BankDetail).filter(BankDetail.id == bank_detail_id).first()
    if not bank_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank detail not found."
        )

    db.delete(bank_detail)
    db.commit()