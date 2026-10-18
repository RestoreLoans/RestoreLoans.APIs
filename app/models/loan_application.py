from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base


# Lifecycle of a loan application, independent of the legacy `loans.status`
# enum column (active/paid/default). Stored as a plain string so new states can
# be added without an ALTER TYPE migration.
STATUS_PENDING_APPROVAL = "pending_approval"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_DISBURSED = "disbursed"
STATUS_COMPLETED = "completed"
STATUS_DEFAULTED = "defaulted"

VALID_APPLICATION_STATUSES = {
    STATUS_PENDING_APPROVAL,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_DISBURSED,
    STATUS_COMPLETED,
    STATUS_DEFAULTED,
}

# Statuses that mean an application is still "in progress" (under review or
# awaiting disbursement). A customer may not edit their profile while one of
# these is active.
IN_PROGRESS_STATUSES = {STATUS_PENDING_APPROVAL, STATUS_APPROVED}


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True, nullable=False)
    loan_id = Column(
        Integer,
        ForeignKey("loans.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status = Column(String(30), nullable=False, default=STATUS_PENDING_APPROVAL)
    decided_by = Column(String(200), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
