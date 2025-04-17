from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    loan_id = Column(Integer, ForeignKey("loans.id"))
    transaction_type = Column(String)
    amount = Column(Float)
    amount_from = Column(Float)  # Ensure this exists in the schema
    # Removed `amount_to` as per the instruction
    currency = Column(String)
    account_number = Column(String)
    status = Column(String)
    date_time = Column(String)
    payment_date = Column(String)
    returned_payment = Column(Float)
    interest_payed = Column(Float)
    period = Column(Integer)
    remarks = Column(String)
