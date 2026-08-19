from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserLoginWithRegistration
from app.services.auth import AuthService
from app.utils.security import verify_password
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.email == user_data.email) |
        (User.id_number == user_data.id_number) |
        (User.phone_number == user_data.phone_number)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email, ID number, or phone number already exists."
        )

    hashed_password = AuthService.hash_password(user_data.password)

    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        id_number=user_data.id_number,
        email=user_data.email,
        phone_number=user_data.phone_number,
        gender=user_data.gender,
        password=hashed_password,
        is_active=user_data.is_active
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login/by-registration", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user_by_login_and_registration(payload: UserLoginWithRegistration, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Normalize both registration numbers for comparison
    db_reg_no = str(user.id_number).strip().lower()
    payload_reg_no = str(payload.registration_no).strip().lower()

    logger.info(f"User {user.email} - DB registration: '{db_reg_no}' vs Payload: '{payload_reg_no}'")

    if db_reg_no != payload_reg_no:
        logger.warning(f"Registration mismatch for {user.email}: expected '{db_reg_no}', got '{payload_reg_no}'")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Registration number does not match"
        )

    logger.info(f"Successful login with registration for user {user.email}")
    return user

@router.get("/debug/check-user/{email}", status_code=status.HTTP_200_OK)
def debug_check_user(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "not_found", "email": email}
    return {
        "status": "found",
        "email": user.email,
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "id_number": user.id_number,
        "id_number_type": type(user.id_number).__name__
    }

@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    return user

@router.get("/", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.put("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    for key, value in user_data.dict(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    db.delete(user)
    db.commit()