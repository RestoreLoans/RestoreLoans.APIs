from sqlalchemy import Column, Integer, String, Boolean, Date, Enum, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone

class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    first_name = Column(String(200), nullable=False)
    last_name = Column(String(200), nullable=False)
    id_number = Column(String(200), nullable=False, unique=True)
    email = Column(String(200), nullable=False, unique=True)
    phone_number = Column(String(200), nullable=False, unique=True)
    gender = Column(Enum(Gender), nullable=False)
    password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(Date, nullable=False, default=datetime.utcnow().date)
      # Define the relationship
    created_at = Column(Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    # Define the relationship
    transactions = relationship("Transaction", back_populates="user")
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    company = relationship("Company", back_populates="users")