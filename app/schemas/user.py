from pydantic import BaseModel, EmailStr
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
        from_attributes= True

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