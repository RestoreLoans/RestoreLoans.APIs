from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    transaction_type = Column(String)
    amount = Column(Float)
    credit = Column(Float)
    debit = Column(Float)
    balance = Column(Float)
    currency = Column(String)
    account_number = Column(String)
    status = Column(String)
    date_time = Column(DateTime)
    payment_date = Column(DateTime)
    returned_payment = Column(Float)
    interest_payed = Column(Float)
    period = Column(Integer)
    remarks = Column(String)

    # Relationships - using string reference instead of direct import
    user = relationship('User', back_populates='transactions')
    loan = relationship("Loan", back_populates="transactions")
