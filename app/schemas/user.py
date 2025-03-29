from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import date
from enum import Enum

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class UserBase(BaseModel):
    email: EmailStr
    phone_number: str

class UserCreate(UserBase):
    first_name: str
    last_name: str
    id_number: str
    gender: Gender
    password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserForgotPassword(BaseModel):
    email: EmailStr

class UserForgotUsername(BaseModel):
    email: EmailStr

class UserOTP(BaseModel):
    phone_number: str
    otp: str

class UserResponse(UserBase):
    id: int
    first_name: str
    last_name: str
    id_number: str
    gender: Gender
    is_active: bool
    created_at: date

    class Config:
        orm_mode = True