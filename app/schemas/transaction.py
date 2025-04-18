from pydantic import BaseModel
from datetime import datetime # <-- Make sure this import exists
from typing import Optional

# ... other imports ...

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    loan_id: int
    transaction_type: Optional[str] = None
    amount: Optional[float] = None
    credit: Optional[float] = None
    debit: Optional[float] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
    account_number: Optional[str] = None
    status: Optional[str] = None
    # Correct the types here:
    date_time: Optional[datetime] = None  # <-- Change from str to datetime (or just datetime if never None)
    payment_date: Optional[datetime] = None # <-- Change from str to datetime (or just datetime if never None)
    returned_payment: Optional[float] = None
    interest_payed: Optional[float] = None
    period: Optional[int] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True # Or orm_mode = True for Pydantic v1
        # This allows Pydantic to read data from ORM model attributes

# Potentially also update TransactionCreate and TransactionUpdate if they handle these fields
class TransactionBase(BaseModel):
    user_id: int
    loan_id: int
    transaction_type: Optional[str] = None
    amount: Optional[float] = None
    credit: Optional[float] = None
    debit: Optional[float] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
    account_number: Optional[str] = None
    status: Optional[str] = None
    date_time: Optional[datetime] = None # <-- Ensure correct type here too
    payment_date: Optional[datetime] = None # <-- Ensure correct type here too
    returned_payment: Optional[float] = None
    interest_payed: Optional[float] = None
    period: Optional[int] = None
    remarks: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass # Inherits correct types

class TransactionUpdate(BaseModel):
    # Define only fields that can be updated, ensure correct types
    transaction_type: Optional[str] = None
    amount: Optional[float] = None
    credit: Optional[float] = None
    debit: Optional[float] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
    account_number: Optional[str] = None
    status: Optional[str] = None
    date_time: Optional[datetime] = None # <-- Ensure correct type here too
    payment_date: Optional[datetime] = None # <-- Ensure correct type here too
    returned_payment: Optional[float] = None
    interest_payed: Optional[float] = None
    period: Optional[int] = None
    remarks: Optional[str] = None

