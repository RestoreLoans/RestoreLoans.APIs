from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class LoanTransaction(Base):
    __tablename__ = "loan_transactions"
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    borrower = Column(String, nullable=False)
    loan_amount = Column(Float, nullable=False)
    status_approval = Column(String, default="Pending")  # Pending, Approved,
    # Declined
    # Add other fields as neededing, default="Pending")  # Pending, Approved, Declined
    date_approved = Column(DateTime, nullable=True)
    # Add other fields as needed