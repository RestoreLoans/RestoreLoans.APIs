from pydantic import BaseModel
from typing import Optional

class TransactionCreate(BaseModel):
    user_id: int
    loan_id: int
    transaction_type: str
    amount: float
    amount_from: Optional[float] = None
    currency: str
    account_number: str
    status: str
    date_time: str
    payment_date: Optional[str] = None
    returned_payment: Optional[float] = None
    interest_payed: Optional[float] = None
    period: Optional[int] = None
    remarks: Optional[str] = None

class TransactionUpdate(BaseModel):
    """
    Schema for updating a transaction.
    """
    id: Optional[int] = None
    user_id: Optional[int] = None
    loan_id: Optional[int] = None
    transaction_type: Optional[str] = None
    amount: Optional[float] = None
    amount_from: Optional[float] = None
    currency: Optional[str] = None
    account_number: Optional[str] = None
    status: Optional[str] = None
    date_time: Optional[str] = None
    payment_date: Optional[str] = None
    returned_payment: Optional[float] = None
    interest_payed: Optional[float] = None
    period: Optional[int] = None
    remarks: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    loan_id: int
    transaction_type: str
    amount: float
    amount_from: float
    currency: str
    account_number: str
    status: str
    date_time: str
    payment_date: str
    returned_payment: float
    interest_payed: float
    period: int
    remarks: Optional[str]

    class Config:
        from_attributes= True
