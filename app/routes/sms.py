from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.sms import SMSResponse
from app.services.auth import AuthService

router = APIRouter(
    prefix="/sms",
    tags=["SMS"]
)

@router.get("/", response_model=list[SMSResponse])
def get_sms(db: Session = Depends(get_db)):
    # Implement SMS retrieval
    pass