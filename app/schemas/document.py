from pydantic import BaseModel
from enum import Enum
from datetime import date

class DocumentStatus(str, Enum):
    pending = "pending"
    uploaded = "uploaded"
    failed = "failed"

class DocumentBase(BaseModel):
    document_name: str
    file_path: str
    file_size: int
    remarks: str = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    user_id: int
    loan_id: int = None
    status: DocumentStatus
    upload_date: date

    class Config:
        from_attributes = True