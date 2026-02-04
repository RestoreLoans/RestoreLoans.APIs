from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class UserStats(BaseModel):
    totalLoans: int
    activeLoans: int
    completedLoans: int
    totalBorrowed: float


class LoanDashboardLoan(BaseModel):
    id: str
    customerName: str
    loanAmount: float
    loanTerm: Optional[int] = None
    monthlyPayment: float
    interestRate: Optional[float] = None
    status: str
    disburseDate: Optional[date] = None
    applicationDate: Optional[date] = None
    outstandingBalance: float
    paidMonths: int
    remainingMonths: int
    accountNumber: Optional[str] = None
    decisionDate: Optional[date] = None
    decisionReason: Optional[str] = None


class PaymentHistoryItem(BaseModel):
    loanId: str
    paymentId: str
    paymentDate: Optional[datetime] = None
    amount: float
    paymentMethod: Optional[str] = None
    status: Optional[str] = None


class LoanDashboardResponse(BaseModel):
    userName: str
    userStats: UserStats
    userLoans: list[LoanDashboardLoan]
    paymentHistory: list[PaymentHistoryItem]
