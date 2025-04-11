from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from app.database import Base
import enum

class DocumentStatus(str, enum.Enum):
    pending = "pending"
    uploaded = "uploaded"
    failed = "failed"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=True)
    file_name = Column(String, nullable=False)
    document_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    status = Column(Enum(DocumentStatus), server_default=DocumentStatus.pending.name, nullable=False)
    upload_date = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    remarks = Column(String, nullable=True)