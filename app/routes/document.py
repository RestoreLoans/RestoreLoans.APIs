from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.document import Document
from app.models.loan import Loan
from app.schemas.document import DocumentResponse
import os

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    user_id: int,
    loan_id: int,
    document_name: str,
    document_status: str,
    remarks: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Check if the loan exists
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with ID {loan_id} does not exist."
        )

    # Save the uploaded file to a directory
    upload_dir = "uploaded_files"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Create a new document instance
    new_document = Document(
        user_id=user_id,
        loan_id=loan_id,
        file_name=file.filename,
        document_name=document_name,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        status=document_status,
        remarks=remarks
    )

    # Add the document to the database
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document