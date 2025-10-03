from fastapi import APIRouter, Depends,UploadFile, HTTPException, status, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.loan import Loan
from app.models.user import User
from app.schemas.loan import LoanCreate, LoanResponse
from google.cloud import storage
import os


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "app/utils/google.json"
router = APIRouter(
    prefix="/loans",
    tags=["Loans"]
)
BUCKET_NAME = "restoreloans"
SERVICE_ACCOUNT_FILE = "app/utils/google_service_account.json"
@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(  loan_type: str = Form(...),
    loan_amount: float = Form(...),
    interest_rate: float = Form(...),
    loan_term: int = Form(...),
    monthly_installment: float = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    user_id: int = Form(...),
    id_document: UploadFile = File(...),
    bank_statement: UploadFile = File(...),
    proof_of_residence: UploadFile = File(...), db: Session = Depends(get_db)):
    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID"
               
        )
    
    # Create a new loan instance
    new_loan = Loan(
        user_id=user_id,
        loan_type=loan_type,
        loan_amount=loan_amount,
        interest_rate=interest_rate,
        loan_term=loan_term,
        monthly_installment=monthly_installment,
        start_date=start_date,
        end_date=end_date,
        status="active",
        id_path =upload_to_gcs(id_document, "id_documents",user_id),
        bank_path=upload_to_gcs(bank_statement, "bank_statements",user_id), 
        proof_of_residence_path = upload_to_gcs(proof_of_residence, "residences",user_id)

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
@router.get("/by-user-id/{user_id}", response_model=LoanResponse, status_code=status.HTTP_200_OK)
def get_loan_by_user(user_id: int, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.user_id == user_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with ID {user_id} does not exist."
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
def upload_to_gcs(file: UploadFile, folder: str = "loans", uid:str="") -> str:
    """Upload file to GCS and return its public URL."""
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    # Generate unique filename
    unique_filename = f"{folder}/{uid}_{file.filename}"

    blob = bucket.blob(unique_filename)
    blob.upload_from_file(file.file, content_type=file.content_type)

    # Make file public
    #blob.make_public()

    return f"https://storage.googleapis.com/{bucket.name}/{unique_filename}"