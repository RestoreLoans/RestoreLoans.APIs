from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.document import DocumentResponse
from app.services.auth import AuthService
import os
from fastapi import HTTPException, status
from app.models.document import Document  # Assuming Document is the SQLAlchemy model for documents
from datetime import datetime

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)
UPLOAD_DIRECTORY = "uploaded_documents"  # Directory to save uploaded files

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Ensure the upload directory exists
    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)

    # Save the uploaded file to the upload directory
    file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save the file: {str(e)}"
        )

    # Create a new document entry in the database
    new_document = Document(
        file_name=file.filename,
        file_path=file_path,
        uploaded_at=datetime.utcnow()
    )

    # Add the document to the database
    db.add(new_document)
    db.commit()
    db.refresh(new_document)  # Refresh to get the updated data from the database

    return new_document