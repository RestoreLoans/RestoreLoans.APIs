from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.document import DocumentResponse
from ..services.auth import AuthService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Implement document upload
    pass