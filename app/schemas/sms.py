from pydantic import BaseModel
from typing import Optional

class SMSCreate(BaseModel):
    sender: str
    recipient: str
    message: str

class SMSUpdate(BaseModel):
    sender: Optional[str] = None
    recipient: Optional[str] = None
    message: Optional[str] = None

class SMSResponse(BaseModel):
    id: int
    sender: str
    recipient: str
    message: str

    class Config:
        from_attributes= True