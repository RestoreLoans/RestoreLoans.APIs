from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class DeliveryStatus(str, Enum):
    sent = "sent"
    delivered = "delivered"
    failed = "failed"

class SMSBase(BaseModel):
    sender: str
    recipient: str
    message: str
    remarks: str = None

class SMSResponse(SMSBase):
    id: int
    user_id: int
    status: DeliveryStatus
    timestamp: datetime

    class Config:
        from_attributes = True