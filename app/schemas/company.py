from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class CompanyBase(BaseModel):
    name: str
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None




class CompanyCreate(CompanyBase):
    name: str
    email: EmailStr
    address: str
    phone: str
    user_id: int


class CompanyResponse(CompanyBase):
    id: int
    address: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
   



    class Config:
        from_attributes = True