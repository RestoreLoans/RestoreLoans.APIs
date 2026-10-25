from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from app.database import Base
from datetime import datetime, timezone


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DocumentRequest(Base):
    __tablename__ = "document_requests"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)  # id_document | bank_statement | proof_of_residence
    requested_by = Column(String(200), nullable=False)
    reason = Column(Text, nullable=True)
    token = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending | uploaded | approved | rejected
    requested_at = Column(DateTime, nullable=False, default=_utcnow)
    uploaded_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_email = Column(String(200), nullable=True)
    review_outcome = Column(Text, nullable=True)
    uploaded_file_path = Column(String(900), nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow)