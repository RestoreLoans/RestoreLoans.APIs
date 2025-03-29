from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..schemas.user import UserLogin, UserCreate, UserOTP, UserForgotPassword, UserForgotUsername, UserResponse
from ..services.auth import AuthService
from ..database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    return AuthService.register_user(db, user_data)

@router.post("/login")
def login(user_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return AuthService.login_user(db, user_data)

@router.post("/forgot-password")
def forgot_password(forgot_data: UserForgotPassword, db: Session = Depends(get_db)):
    return AuthService.forgot_password(db, forgot_data.email)

@router.post("/forgot-username")
def forgot_username(forgot_data: UserForgotUsername, db: Session = Depends(get_db)):
    return AuthService.forgot_username(db, forgot_data.email)

@router.post("/verify-otp")
def verify_otp(otp_data: UserOTP, db: Session = Depends(get_db)):
    return AuthService.verify_otp(db, otp_data.phone_number, otp_data.otp)