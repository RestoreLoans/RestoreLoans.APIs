from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from app.database import Base
import enum

class AlertType(str, enum.Enum):
    warning = "warning"
    error = "error"
    notification = "notification"
    success = "success"

class PriorityLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"

class AlertStatus(str, enum.Enum):
    active = "active"
    dismissed = "dismissed"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False)
    message = Column(String, nullable=False)
    date_time = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    priority = Column(Enum(PriorityLevel), nullable=False)
    status = Column(Enum(AlertStatus), server_default="active", nullable=False)
    action_required = Column(Boolean, server_default='TRUE', nullable=False)
    remarks = Column(String, nullable=True)