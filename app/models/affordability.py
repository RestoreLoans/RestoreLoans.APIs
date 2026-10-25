from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from app.database import Base
from datetime import datetime, timezone


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AffordabilityAssessment(Base):
    __tablename__ = "affordability_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    gross_monthly_income = Column(Float, default=0)
    net_monthly_income = Column(Float, default=0)
    additional_income = Column(Float, default=0)
    housing_expense = Column(Float, default=0)
    utilities_expense = Column(Float, default=0)
    transport_expense = Column(Float, default=0)
    food_expense = Column(Float, default=0)
    insurance_expense = Column(Float, default=0)
    school_fees_expense = Column(Float, default=0)
    existing_loans_expense = Column(Float, default=0)
    other_expenses = Column(Float, default=0)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)