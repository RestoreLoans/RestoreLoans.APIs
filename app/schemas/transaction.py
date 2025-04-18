from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionBase(BaseModel):
    user_id: int
    loan_id: int
    transaction_type: Optional[str] = None
    amount: float  # <--- REMOVE Optional[...] = None. Make it required.
    credit: Optional[float] = None
    debit: Optional[float] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
    account_number: Optional[str] = None
    status: Optional[str] = None
    date_time: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    returned_payment: Optional[float] = None
    interest_payed: Optional[float] = None
    period: Optional[int] = None
    remarks: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass # Now inherits the REQUIRED amount field

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    loan_id: int
    transaction_type: Optional[str] = None
    amount: Optional[float] = None # Keep Optional here if response can sometimes omit it, or make required if always present
    credit: Optional[float] = None
    debit: Optional[float] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
    account_number: Optional[str] = None
    status: Optional[str] = None
    date_time: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    returned_payment: Optional[float] = None
    interest_payed: Optional[float] = None
    period: Optional[int] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True

class TransactionUpdate(BaseModel):
    # Keep Optional here as updates might not include amount
    transaction_type: Optional[str] = None
    amount: Optional[float] = None
    credit: Optional[float] = None
    debit: Optional[float] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
    account_number: Optional[str] = None
    status: Optional[str] = None
    date_time: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    returned_payment: Optional[float] = None
    interest_payed: Optional[float] = None
    period: Optional[int] = None
    remarks: Optional[str] = None
