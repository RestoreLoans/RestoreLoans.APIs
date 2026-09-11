from pydantic import BaseModel, EmailStr
from typing import List, Optional

class SendLoanEmailRequest(BaseModel):
    transaction_id: int
    recipient_emails: Optional[List[EmailStr]] = None
    email_type: str
    custom_message: Optional[str] = None
    rejection_reason: Optional[str] = None

class SendApplicationDocsEmailRequest(BaseModel):
    transaction_id: Optional[int] = None