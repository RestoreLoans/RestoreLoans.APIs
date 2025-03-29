from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from app.database import Base
import enum

class AccountType(str, enum.Enum):
    savings = "savings"
    current = "current"
    cheque = "cheque"

class BankDetail(Base):
    __tablename__ = "bank_details"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bank_name = Column(String, nullable=False)
    branch_name = Column(String, nullable=False)
    branch_code = Column(String, nullable=False)
    account_holder_name = Column(String, nullable=False)
    account_number = Column(String, nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))