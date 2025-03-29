from pydantic import BaseModel
from enum import Enum

class AccountType(str, Enum):
    savings = "savings"
    current = "current"
    cheque = "cheque"

class BankBase(BaseModel):
    bank_name: str
    branch_name: str
    branch_code: str
    account_holder_name: str
    account_number: str
    account_type: AccountType

class BankCreate(BankBase):
    pass

class BankResponse(BankBase):
    id: int
    user_id: int
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True