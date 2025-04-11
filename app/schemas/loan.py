from pydantic import BaseModel
from datetime import date
from enum import Enum

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

class LoanCreate(LoanBase):
    user_id: int  # The ID of the user associated with the loan

class LoanResponse(LoanBase):
    id: int
    user_id: int
    status: LoanStatus
    created_at: date

    class Config:
        from_attributes = True