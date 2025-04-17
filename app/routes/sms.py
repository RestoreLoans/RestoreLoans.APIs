from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.sms import SMSResponse, SMSCreate, SMSUpdate
from app.models.sms import SMS  # Assuming SMS is the SQLAlchemy model for SMS records

router = APIRouter(
    prefix="/sms",
    tags=["SMS"]
)

@router.get("/", response_model=list[SMSResponse])
def get_sms(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    # Query SMS
    sms_records = db.query(SMS).offset(skip).limit(limit).all()

    # Return the list of SMS records
    return sms_records


@router.get("/{sms_id}", response_model=SMSResponse)
def get_sms_by_id(sms_id: int, db: Session = Depends(get_db)):
    # Query SMS by ID
    sms_record = db.query(SMS).filter(SMS.id == sms_id).first()
    if not sms_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMS not found")
    return sms_record


@router.post("/", response_model=SMSResponse, status_code=status.HTTP_201_CREATED)
def create_sms(sms: SMSCreate, db: Session = Depends(get_db)):
    # Create a new SMS record
    new_sms = SMS(**sms.model_dump())
    db.add(new_sms)
    db.commit()
    db.refresh(new_sms)

    # Return the created SMS record
    return new_sms


@router.put("/{sms_id}", response_model=SMSResponse)
def update_sms(sms_id: int, sms: SMSUpdate, db: Session = Depends(get_db)):
    # Query SMS by ID
    sms_record = db.query(SMS).filter(SMS.id == sms_id).first()
    if not sms_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMS not found")

    # Update SMS record
    for key, value in sms.model_dump(exclude_unset=True).items():
        setattr(sms_record, key, value)
    db.commit()
    db.refresh(sms_record)

    # Return the updated SMS record
    return sms_record


@router.delete("/{sms_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sms(sms_id: int, db: Session = Depends(get_db)):
    # Query SMS by ID
    sms_record = db.query(SMS).filter(SMS.id == sms_id).first()
    if not sms_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMS not found")

    # Delete SMS record
    db.delete(sms_record)
    db.commit()