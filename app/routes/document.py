from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
# Import the Enum from models or schemas
from app.models.document import Document, DocumentStatus # Import Enum
from app.models.loan import Loan
from app.models.user import User
# Import corrected schemas
from app.schemas.document import DocumentResponse, DocumentCreate, DocumentUpdate
import os
import logging # Optional: for logging errors

# Setup logger (optional)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

# Create (Upload Document)
@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    # Use Depends() for form data fields
    document_data: DocumentCreate = Depends(), # <--- FIX 1
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Check if the loan exists using document_data
    loan = db.query(Loan).filter(Loan.id == document_data.loan_id).first() # <--- FIX 2
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan with ID {document_data.loan_id} does not exist." # <--- FIX 2
        )

    # Check if user exists (Optional but recommended)
    user = db.query(User).filter(User.id == document_data.user_id).first() # <--- FIX 2 (already correct here)
    if not user:
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail=f"User with ID {document_data.user_id} does not exist." # <--- FIX 2
         )

    # Save the uploaded file to a directory
    upload_dir = "uploaded_files"
    os.makedirs(upload_dir, exist_ok=True)
    # Consider making filenames unique (e.g., using UUID)
    file_path = os.path.join(upload_dir, file.filename)
    file_size = 0

    try:
        # Read file content and write
        content = file.file.read() # Read content first
        file_size = len(content) # Get size from content length
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        logger.error(f"Failed to save uploaded file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        # Ensure file handle is closed even if read/write fails
        if file and not file.file.closed:
             file.file.close()

    # Determine status: use input if provided, otherwise default to uploaded
    doc_status = document_data.document_status if document_data.document_status is not None else DocumentStatus.uploaded # <--- FIX 3

    # Create a new document instance using data from document_data and file info
    new_document_data = {
        "user_id": document_data.user_id, # <--- FIX 2
        "loan_id": document_data.loan_id, # <--- FIX 2
        "file_name": file.filename,
        "document_name": document_data.document_name, # <--- FIX 2
        "file_path": file_path,
        "file_size": file_size,
        "status": doc_status, # Use determined status
        "remarks": document_data.remarks # <--- FIX 2
    }
    new_document = Document(**new_document_data)

    # Add the document to the database
    db.add(new_document)
    try:
        db.commit() # <--- FIX 4 (Error handling)
        db.refresh(new_document)
    except Exception as e:
        db.rollback() # <--- FIX 4
        logger.error(f"Failed to commit document record for {file.filename}: {e}")
        # Clean up the saved file if the DB commit fails
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as remove_err:
                logger.error(f"Failed to remove file {file_path} after DB error: {remove_err}")
        raise HTTPException(status_code=500, detail=f"Could not save document record: {e}")

    return new_document

# --- Other routes (GET, PUT, DELETE) ---
# Remember to add try/except/rollback to PUT and DELETE commit operations
# Use .model_dump(exclude_unset=True) in PUT route if using Pydantic v2+

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

    # Use model_dump for Pydantic v2+
    update_data = document_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(document, key, value)

    try: # <--- FIX 4
        db.commit()
        db.refresh(document)
    except Exception as e: # <--- FIX 4
        db.rollback()
        logger.error(f"Failed to update document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not update document record: {e}")

    return document

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} does not exist."
        )

    file_path_to_delete = document.file_path # Store path before potential deletion

    try: # <--- FIX 4
        db.delete(document)
        db.commit()
    except Exception as e: # <--- FIX 4
         db.rollback()
         logger.error(f"Failed to delete document record {document_id}: {e}")
         raise HTTPException(status_code=500, detail=f"Could not delete document record: {e}")

    # Delete the file from the file system AFTER successful DB deletion
    if os.path.exists(file_path_to_delete):
        try:
            os.remove(file_path_to_delete)
        except Exception as e:
            # Log this error, but don't fail the request as DB record is gone
            logger.error(f"Failed to remove file {file_path_to_delete} for deleted document {document_id}: {e}")

    # Use status code directly or return Response(status_code=204)
    # return # Implicitly returns None with 204 status code

