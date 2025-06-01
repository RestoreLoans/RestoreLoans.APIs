
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import User  # Import User model
from app.models.loan import Loan  # Import Loan model

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # Foreign key to users table
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    transaction_type = Column(String(200))
    amount = Column(Float, nullable=True)
    credit = Column(Float)
    debit = Column(Float)
    balance = Column(Float)
    currency = Column(String(200))
    account_number = Column(String(200))
    status = Column(String(200))
    date_time = Column(DateTime)
    payment_date = Column(DateTime)
    returned_payment = Column(Float)
    interest_payed = Column(Float)
    period = Column(Integer)
    remarks = Column(String(200))

    # Relationships
    user = relationship('User', back_populates='transactions') # Add this relationship
    loan = relationship("Loan", back_populates="transactions")