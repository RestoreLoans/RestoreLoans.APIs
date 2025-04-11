from pydantic import BaseModel, validator
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
    remarks: str = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    user_id: int
    loan_id: int = None
    status: DocumentStatus
    upload_date: date

    @validator("upload_date", pre=True)
    def parse_datetime_to_date(cls, value):
        if isinstance(value, datetime):
            return value.date()
        return value

    class Config:
        orm_mode = True