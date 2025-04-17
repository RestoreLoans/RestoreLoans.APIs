from pydantic import BaseModel, field_validator
from typing import Optional
from enum import Enum
from datetime import date, datetime

class DocumentStatus(str, Enum):
    pending = "pending"
    uploaded = "uploaded"
    failed = "failed"

class DocumentBase(BaseModel):
    document_name: str
    file_name: str  # Added file_name to match the JSON
    file_path: str
    file_size: int
    remarks: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    user_id: int
    loan_id: Optional[int] = None
    status: DocumentStatus
    upload_date: date

    @field_validator("upload_date", mode="before")
    def parse_datetime_to_date(cls, value):
        if isinstance(value, datetime):
            return value.date()
        return value

    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    document_name: Optional[str] = None
    document_status: Optional[str] = None
    remarks: Optional[str] = None