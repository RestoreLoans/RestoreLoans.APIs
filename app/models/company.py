from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import User  # Ensure this import exists

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)
    pay_day_date = Column(Date, nullable=True)
    address1 = Column(String, nullable=True)
    address2 = Column(String, nullable=True)
    town = Column(String, nullable=True)
    suburb = Column(String, nullable=True)
    post_code = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    appointed_on_date = Column(Date, nullable=True)
    pay_date_shift = Column(String, nullable=True)
    contact_method = Column(String, nullable=True)
    salary_freq = Column(String, nullable=True)
    pay_method = Column(String, nullable=True)
    pay_day_of_week = Column(Integer, nullable=True)
    contract_end_date = Column(Date, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])