from pydantic import BaseModel
from datetime import date, datetime
from enum import Enum
from typing import Optional

class LoanType(str, Enum):
    home = "home"
    car = "car"
    personal = "personal"

class LoanStatus(str, Enum):
    active = "active"
    paid = "paid"
    default = "default"

class LoanBase(BaseModel):
    loan_type: LoanType
    loan_amount: float
    interest_rate: float
    loan_term: int  # in months
    monthly_installment: float
    start_date: date
    end_date: date
    id_path: str
    bank_path: str
    proof_of_residence_path: str

class LoanCreate(LoanBase):
    user_id: int  # The ID of the user associated with the loan

class LoanResponse(LoanBase):
    id: int
    user_id: int
    status: LoanStatus
    created_at: datetime
    id_path: Optional[str] = None
    bank_path: Optional[str] = None
    proof_of_residence_path: Optional[str] = None

    class Config:
        from_attributes = True