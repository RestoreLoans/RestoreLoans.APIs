from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from app.models.user import Gender

class UserBase(BaseModel):
    first_name: str
    last_name: str
    id_number: str
    email: EmailStr
    phone_number: str
    gender: Gender
    is_active: bool

class UserCreate(UserBase):
    password: str  # Password is required when creating a user

class UserResponse(UserBase):
    id: int
    created_at: date

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