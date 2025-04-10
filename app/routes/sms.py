from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.sms import SMSResponse
from app.services.auth import AuthService
from app.models.sms import SMS  # Assuming SMS is the SQLAlchemy model for SMS records
from fastapi import HTTPException, status

router = APIRouter(
    prefix="/sms",
    tags=["SMS"]
)

@router.get("/", response_model=list[SMSResponse])
def get_sms(db: Session = Depends(get_db)):
    # Query all SMS records from the database
    sms_records = db.query(SMS).all()

    # Return the list of SMS records
    return sms_records