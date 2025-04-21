# In app/schemas/document.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime # Import datetime

# Re-add the Enum definition if not imported from models
class DocumentStatus(str, Enum):
    pending = "pending"
    uploaded = "uploaded"
    failed = "failed"

# --- Corrected DocumentCreate ---
class DocumentCreate(BaseModel):
    # Fields client MUST provide in the form data
    user_id: int
    loan_id: int
    document_name: str # e.g., "Payslip July 2024"

    # Optional fields client CAN provide
    remarks: Optional[str] = None
    # Decide if client can set status on upload, or if it's always 'uploaded'
    document_status: Optional[DocumentStatus] = None

# --- Corrected DocumentResponse ---
class DocumentResponse(BaseModel):
    id: int
    user_id: int
    loan_id: Optional[int] = None # Match model's nullability
    document_name: str
    file_name: str
    file_path: str
    file_size: int
    status: DocumentStatus
    upload_date: datetime # Match model's TIMESTAMP type
    remarks: Optional[str] = None

    class Config:
        from_attributes = True # Use this for Pydantic v2+

# --- Corrected DocumentUpdate ---
class DocumentUpdate(BaseModel):
    document_name: Optional[str] = None
    # Use the Enum for status updates
    document_status: Optional[DocumentStatus] = None
    remarks: Optional[str] = None
