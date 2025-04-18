from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.sms import DeliveryStatus


class SMSCreate(BaseModel):
    user_id: int  # <--- ADD THIS LINE
    sender: str
    recipient: str
    message: str
    remarks: Optional[str] = None

class SMSUpdate(BaseModel):
    # user_id is usually not updatable, so keep it out of Update
    sender: Optional[str] = None
    recipient: Optional[str] = None
    message: Optional[str] = None
    remarks: Optional[str] = None # Add if remarks should be updatable

class SMSResponse(BaseModel):
    id: int
    user_id: int # <--- Make sure user_id is also in the response
    sender: str
    recipient: str
    message: str
    timestamp: datetime
    status: DeliveryStatus
    remarks: Optional[str] = None

    class Config:
        from_attributes = True # or orm_mode = True for Pydantic v1
