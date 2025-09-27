from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoanTransactionBase(BaseModel):
    loan_id: int
    user_id: int
    borrower: str
    loan_amount: float


class LoanTransactionCreate(LoanTransactionBase):
    pass


class LoanTransactionUpdateStatus(BaseModel):
    status_approval: str  # "Pending", "Approved", "Declined"


class LoanTransactionResponse(LoanTransactionBase):
    id: int
    date_applied: datetime
    status_approval: str
    date_approved: Optional[datetime] = None

    class Config:
        from_attributes = True