from sqlalchemy import Column, Integer, String, Enum, Float, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from ..database import Base
import enum

class TransactionType(str, enum.Enum):
    credit = "credit"
    debit = "debit"
    transfer = "transfer"
    payment = "payment"

class TransactionStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, server_default="ZAR", nullable=False)
    account_number = Column(String, nullable=False)
    status = Column(Enum(TransactionStatus), server_default="pending", nullable=False)
    date_time = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    remarks = Column(String, nullable=True)