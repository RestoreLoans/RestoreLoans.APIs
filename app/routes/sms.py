from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.sms import SMSResponse, SMSCreate, SMSUpdate
from app.models.sms import SMS  # Assuming SMS is the SQLAlchemy model for SMS records

router = APIRouter(
    prefix="/sms",
    tags=["SMS"]
)

@router.post("/", response_model=SMSResponse, status_code=status.HTTP_201_CREATED)
def create_sms(sms: SMSCreate, db: Session = Depends(get_db)):
    # --- START VALIDATION ---
    # Check if the user_id provided in the request exists in the users table
    user = db.query(User).filter(User.id == sms.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Or 400 Bad Request
            detail=f"User with ID {sms.user_id} not found."
        )
     # --- END VALIDATION ---

    # If user exists, proceed to create the SMS record
    new_sms = SMS(**sms.model_dump())
    db.add(new_sms)
    try:
        db.commit()
        db.refresh(new_sms)
    except Exception as e: # Catch potential commit errors (though FK should be caught by check now)
         db.rollback()
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail=f"Failed to create SMS record: {e}"
         )
    return new_sms

@router.get("/{sms_id}", response_model=SMSResponse)
def get_sms_by_id(sms_id: int, db: Session = Depends(get_db)):
    # Query SMS by ID
    sms_record = db.query(SMS).filter(SMS.id == sms_id).first()
    if not sms_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMS not found")
    return sms_record


@router.post("/", response_model=SMSResponse, status_code=status.HTTP_201_CREATED)
def create_sms(sms: SMSCreate, db: Session = Depends(get_db)):
    # sms (type SMSCreate) doesn't have user_id
    new_sms = SMS(**sms.model_dump()) # So user_id becomes None here
    db.add(new_sms)
    db.commit() # <-- Error happens here
    db.refresh(new_sms)
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