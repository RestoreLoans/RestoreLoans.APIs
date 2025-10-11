from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class LoanTransactionBase(BaseModel):
    loan_id: int
    user_id: int
    borrower: str
    loan_amount: float
    account_no: Optional[str] = None

class LoanTransactionCreate(LoanTransactionBase):
    pass

class LoanTransactionUpdateStatus(BaseModel):
    status_approval: str

class LoanTransactionResponse(LoanTransactionBase):
    id: int
    date_applied: Optional[datetime] = None
    status_approval: str
    date_approved: Optional[datetime] = None

    class Config:
        from_attributes = True