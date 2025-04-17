from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.document import Document
from app.models.loan import Loan
from app.schemas.document import DocumentResponse, DocumentCreate, DocumentUpdate
import os

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

# Create (Upload Document)
@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    document: DocumentCreate,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Check if the loan exists
    loan = db.query(Loan).filter(Loan.id == document.loan_id).first()
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with ID {document.loan_id} does not exist."
        )

    # Save the uploaded file to a directory
    upload_dir = "uploaded_files"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Create a new document instance
    new_document = Document(
        user_id=document.user_id,
        loan_id=document.loan_id,
        file_name=file.filename,
        document_name=document.document_name,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        status=document.document_status,
        remarks=document.remarks
    )

    # Add the document to the database
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document

# Read (Get Document by ID)
@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} does not exist."
        )
    return document

# Update (Update Document by ID)
@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} does not exist."
        )

    for key, value in document_update.dict(exclude_unset=True).items():
        setattr(document, key, value)

    db.commit()
    db.refresh(document)
    return document

# Delete (Delete Document by ID)
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} does not exist."
        )

    # Delete the file from the file system
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()
    return