from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserResponse
from app.services.auth import AuthService

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/me", response_model=UserResponse)
def get_current_user(db: Session = Depends(get_db)):
    # Implement user retrieval
    pass

# @router.get("/me", response_model=UserResponse)
# def get_current_user(db: Session = Depends(get_db), current_user: User = Depends(AuthService.get_current_user)):
#     # Retrieve the current user from the database
#     user = db.query(User).filter(User.id == current_user.id).first()

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )

#     return user