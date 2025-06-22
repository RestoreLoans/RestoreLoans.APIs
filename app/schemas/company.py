from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class CompanyBase(BaseModel):
    name: str
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class CompanyCreate(CompanyBase):
    name: str
    email: EmailStr

class CompanyResponse(CompanyBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True