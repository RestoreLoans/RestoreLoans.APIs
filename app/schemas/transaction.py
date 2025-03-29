from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class TransactionType(str, Enum):
    credit = "credit"
    debit = "debit"
    transfer = "transfer"
    payment = "payment"

class TransactionStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class TransactionBase(BaseModel):
    transaction_type: TransactionType
    amount: float
    currency: str = "ZAR"
    account_number: str
    remarks: str = None

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    loan_id: int = None
    status: TransactionStatus
    date_time: datetime

    class Config:
        from_attributes = True