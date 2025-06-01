from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from app.database import Base
import enum

class DeliveryStatus(str, enum.Enum):
    sent = "sent"
    delivered = "delivered"
    failed = "failed"

class SMS(Base):
    __tablename__ = "sms"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(200), nullable=False)
    recipient = Column(String(200), nullable=False)
    message = Column(String(200), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    status = Column(Enum(DeliveryStatus), server_default="sent", nullable=False)
    remarks = Column(String(200), nullable=True)