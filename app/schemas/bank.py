from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class AccountType(str, Enum):
    savings = "savings"
    current = "current"
    cheque = "cheque"

class BankDetailBase(BaseModel):
    bank_name: str
    branch_name: str
    branch_code: str
    account_holder_name: str
    account_number: str
    account_type: AccountType

class BankDetailCreate(BankDetailBase):
    user_id: int  # The ID of the user associated with the bank detail

class BankDetailResponse(BankDetailBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes= True