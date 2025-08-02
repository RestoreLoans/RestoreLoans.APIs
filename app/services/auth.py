from datetime import datetime, timedelta
from typing import Optional

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from ..models.user import User
from ..schemas.user import UserCreate, UserResponse
from ..utils.security import create_access_token, verify_password, get_password_hash
import random
import hashlib
import string
from app.schemas.user import UserResponse
from app.schemas.userRoles import UserRoleResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def some_method():
        pass  # Replace with actual implementation or remove if unnecessary

    def register_user(db: Session, user_data: UserCreate):
        # Check if email already exists
        db_user = db.query(User).filter(User.email == user_data.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Check if ID number already exists
        db_user = db.query(User).filter(User.id_number == user_data.id_number).first()
        if db_user:
            raise HTTPException(status_code=400, detail="ID number already registered")

        # Check if phone number already exists
        db_user = db.query(User).filter(User.phone_number == user_data.phone_number).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Phone number already registered")

        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create new user
        db_user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            id_number=user_data.id_number,
            email=user_data.email,
            phone_number=user_data.phone_number,
            gender=user_data.gender,
            password=hashed_password
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user



    @staticmethod
    def login_user(db: Session, user_data: OAuth2PasswordRequestForm):
        user = db.query(User).filter(User.email == user_data.email).first()
        if not user or not verify_password(user_data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            

        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer","user": user}

    @staticmethod
    def forgot_password(db: Session, email: str):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Email not found")

        # Generate OTP (in a real app, store this with expiry)
        otp = ''.join(random.choices(string.digits, k=6))
        return {"message": "OTP sent to registered phone", "otp": otp}  # Don't return OTP in production

    @staticmethod
    def forgot_username(db: Session, email: str):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Email not found")
        return {"message": "Username sent to registered email"}

    @staticmethod
    def verify_otp(db: Session, phone_number: str, otp: str):
        # In real app, verify against stored OTP
        if len(otp) != 6 or not otp.isdigit():
            raise HTTPException(status_code=400, detail="Invalid OTP format")
        return {"message": "OTP verified successfully"}

    @staticmethod
    def user_roles(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        roles = db.query(UserRoleResponse).filter(UserRoleResponse.user_id == user_id).all()
        return {"user": UserResponse.from_orm(user), "roles": roles}
    
    @staticmethod
    def hash_password(password: str) -> str:
        # Hash the password using SHA-256
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    