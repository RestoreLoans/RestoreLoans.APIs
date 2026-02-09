from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from app.models.user import Gender
from .company import CompanyBase
from .bank import BankDetailBase

class ClientDetails(BaseModel):
    idNumber: str
    cellphoneNumber: str
    homephone: Optional[str] = None
    homeAdd1: Optional[str] = None
    homeAdd2: Optional[str] = None
    suburb: Optional[str] = None
    town: Optional[str] = None
    code: Optional[str] = None
    title: Optional[str] = None
    name: str
    surname: str
    email: EmailStr
    password: str
    language: Optional[str] = None
    dob: Optional[date] = None  # Pydantic will auto-parse ISO date strings
    nationality: Optional[int] = None
    gender: str

class EmployerDetails(BaseModel):
    name: str
    type: Optional[str] = None
    payDayDate: Optional[str] = None  # yyyy/mm/dd
    address1: Optional[str] = None
    address2: Optional[str] = None
    town: Optional[str] = None
    suburb: Optional[str] = None
    postCode: Optional[str] = None
    phone: Optional[str] = None
    appointedOnDate: Optional[str] = None
    payDateShift: Optional[str] = None
    contactMethod: Optional[str] = None
    salaryFeq: Optional[str] = None
    payMethod: Optional[str] = None
    payDayOfWeek: Optional[int] = None
    contractEndDate: Optional[str] = None

class BankDetails(BaseModel):
    bank_name: str
    branch_name: Optional[str] = None
    branch_code: Optional[str] = None
    account_holder_name: Optional[str] = None
    account_number: str
    account_type: str  # Should match Enum(AccountType) if used
    created_at: Optional[date] = None
    updated_at: Optional[date] = None

class RegisterPayload(BaseModel):
    clientDetails: ClientDetails
    employerDetails: EmployerDetails
    bankDetails: BankDetails

class UserBase(BaseModel):
    first_name: str
    last_name: str
    id_number: str
    email: EmailStr
    phone_number: str
    gender: Gender
    title: Optional[str] = None
    homephone: Optional[str] = None
    home_add1: Optional[str] = None
    home_add2: Optional[str] = None
    suburb: Optional[str] = None
    town: Optional[str] = None
    postal_code: Optional[str] = None
    language: Optional[str] = None
    dob: Optional[date] = None
    nationality: Optional[int] = None
    is_active: bool
    company_id: Optional[int] = None
    bank_id: Optional[int] = None

    class Config:
        from_attributes = True
    



class UserCreate(UserBase):
    password: str  # Password is required when creating a user

class UserResponse(UserBase):
    id: int
    created_at: date
    company_id: Optional[int] = None


    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOTP(BaseModel):
    email: EmailStr
    otp: str

class UserForgotPassword(BaseModel):
    email: EmailStr
    new_password: str
    confirm_password: str

class UserForgotUsername(BaseModel):
    email: EmailStr

class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    id_number: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    gender: Optional[str]
    is_active: Optional[bool]

    class Config:
        from_attributes= True