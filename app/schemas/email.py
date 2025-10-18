from pydantic import BaseModel, EmailStr
from typing import List, Optional

class SendLoanEmailRequest(BaseModel):
    transaction_id: int
    recipient_emails: List[EmailStr]
    email_type: str  # 'application', 'approval', 'rejection', 'custom'
    custom_message: Optional[str] = None
    rejection_reason: Optional[str] = None