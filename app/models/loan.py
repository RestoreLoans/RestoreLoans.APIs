from sqlalchemy import Column, Integer, Float, Date, Enum, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from app.database import Base
import enum

class LoanType(str, enum.Enum):
    home = "home"
    car = "car"
    personal = "personal"

class LoanStatus(str, enum.Enum):
    active = "active"
    paid = "paid"
    default = "default"

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    loan_type = Column(Enum(LoanType), nullable=False)
    loan_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=True)
    loan_term = Column(Integer, nullable=True)  # in months
    loan_type = Column(String(200))
    monthly_installment = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(LoanStatus), server_default="active", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    transactions = relationship("Transaction", back_populates="loan")
    id_path = Column(String(900))
    bank_path = Column(String(900))
    proof_of_residence_path = Column(String(900))
   