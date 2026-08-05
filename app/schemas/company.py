from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date


class CompanyBase(BaseModel):
    name: str
    type: Optional[str] = None
    pay_day_date: Optional[date] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    town: Optional[str] = None
    suburb: Optional[str] = None
    post_code: Optional[str] = None
    phone: Optional[str] = None
    appointed_on_date: Optional[date] = None
    pay_date_shift: Optional[str] = None
    contact_method: Optional[str] = None
    salary_freq: Optional[str] = None
    pay_method: Optional[str] = None
    pay_day_of_week: Optional[int] = None
    contract_end_date: Optional[date] = None
    user_id: Optional[int] = None


class CompanyCreate(CompanyBase):
    name: str
    user_id: int


class CompanyResponse(CompanyBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True